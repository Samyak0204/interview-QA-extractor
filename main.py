import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from sheets_helper import read_sheets, update_row_status, append_qa_to_sheets
from drive_helper import download_video, extract_file
from audio_extractor import extract_audio
from gemini_helper import extract_qa_from_audio

load_dotenv()

app = FastAPI(title="Interview Q&A Extractor")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.get("/api/interviews")
async def get_interviews():
    sheet_id=os.getenv("SPREADSHEET_ID")
    range_name = os.getenv("SHEET_RANGE", "Sheet1!A1:D100")

    if not sheet_id:
        return {"success": False, "error": "SPREADSHEET_ID is not configured in your .env file."}
    
    try:
        loop = asyncio.get_running_loop()
        interviews = await loop.run_in_executor(None, read_sheets, sheet_id, range_name)
        return {"success": True, "data": interviews}
    except Exception as e:
        return {"success": False, "error": f"An error occurred: {e}"}
    

@app.get("/api/process/stream")
async def process_stream():
    async def event_generator():
        sheet_id = os.getenv("SPREADSHEET_ID")
        range_name = os.getenv("SHEET_RANGE", "Sheet1!A1:D100")
        
        temp_dir = "videos"
        output_dir = "audios"
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        loop = asyncio.get_event_loop()

        yield"data: Fetching pending interviews from Google Sheets...\n\n"
        await asyncio.sleep(0.1)

        try:
            interviews = await loop.run_in_executor(None, read_sheets, sheet_id, range_name)
        except Exception as e:
            yield f"data: Error fetching interviews: {e}\n\n"
            return

        pending_interviews = [r for r in interviews if r.get("Status","").strip().lower() != "completed"]
        yield f"data: Found {len(interviews)} total rows. {len(pending_interviews)} pending interviews.\n\n"
        await asyncio.sleep(0.1)

        if not pending_interviews:
            yield "data: No pending interviews to process.\n\n"
            return
        
        for row in pending_interviews:
            row_num = row.get("row_num")
            interviewer = row.get("Interviewer_ID")
            interviewee = row.get("Interviewee_ID")
            link = row.get("Link")

            yield f"data: \n\n"
            yield f"data: ==================================================\n\n"
            yield f"data: Processing Row {row_num}: Interviewer: {interviewer} | Interviewee: {interviewee}\n\n"
            await asyncio.sleep(0.1)

            file_id = extract_file(link)
            temp_video_path = os.path.join(temp_dir, f"temp_{row_num}.mp4")
            output_audio_path = os.path.join(output_dir, f"{interviewer}_{interviewee}.mp3")

            yield f"data: Downloading video from Drive (File ID: {file_id})...\n\n"
            await asyncio.sleep(0.1)
            download_success = await loop.run_in_executor(None, download_video, file_id, temp_video_path)

            if not download_success:
                yield f"data: Failed to download video. Skipping...\n\n"
                continue

            yield f"data: Extracting MP3 audio from video...\n\n"
            await asyncio.sleep(0.1)
            audio_success = await loop.run_in_executor(None, extract_audio, temp_video_path, output_audio_path)

            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                yield f"data: Cleaned up temporary video file.\n\n"
            
            if not audio_success:
                yield f"data: Audio extraction failed. Skipping...\n\n"
                continue

            yield f"data: Uploading audio to Google Gemini API & extracting Q&As...\n\n"

            await asyncio.sleep(0.1)
            try:
                qa_list = await loop.run_in_executor(None, extract_qa_from_audio, output_audio_path)
                yield f"data: Gemini succesfully extracted {len(qa_list)} Q&As.\n\n"
            except Exception as e:
                yield f"data: Gemini extraction failed: {e}. Skipping...\n\n"
                continue

            yield f"data: Appending structured data to worksheets...\n\n"
            await asyncio.sleep(0.1)
            try:
                await loop.run_in_executor(None, append_qa_to_sheets, sheet_id, interviewer, interviewee, qa_list)
                await loop.run_in_executor(None, update_row_status, sheet_id, row_num, "Completed")
                yield f"data: Row {row_num} successfully processed.\n\n"
            except Exception as e:
                yield f"data: Error writing to Google Sheets: {e}\n\n"

        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
            yield f"data: Cleaned up temporary video file.\n\n"

        yield "data: Pipeline execution completed successfully.\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")