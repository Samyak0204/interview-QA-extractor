import os
import shutil
from dotenv import load_dotenv
from sheets_helper import read_sheets, update_row_status
from drive_helper import download_video, extract_file
from audio_extractor import extract_audio

load_dotenv()

def main():
    sheet_id = os.getenv("SPREADSHEET_ID")
    range_name = os.getenv("SHEET_RANGE", "Sheet1!A1:D100")

    if not sheet_id:
        print("Error: SPREADSHEET_ID not configured in .env file.")
        return
    
    temp_dir = "videos"
    output_dir = "audios"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print("Fetching interview metadata from Google Sheets...")
    try:
        interviews = read_sheets(sheet_id, range_name)
    except Exception as e:
        print(f"Failed to read Google Sheets: {e}")
        return
    
    print(f"Found {len(interviews)} rows. Processing pending interviews...\n")

    for row in interviews:
        row_num = row.get("row_num")
        interviewer = row.get("Interviewer_ID")
        interviewee = row.get("Interviewee_ID")
        link = row.get("Link")
        status = row.get("Status","").strip()

        print(f"--- Row {row_num}: Interviewer: {interviewer} | Interviewee: {interviewee} ---")

        if status.lower()=="completed":
            print(f"Skipping row {row_num} (already completed).")
            continue

        file_id = extract_file(link)
        temp_video_path = os.path.join(temp_dir, f"temp_{row_num}.mp4")
        output_audio_path = os.path.join(output_dir, f"{interviewer}_{interviewee}.mp3")

        print(f"Processing row {row_num}...")

        download_success = download_video(file_id, temp_video_path)
        if not download_success:
            print(f"Failed to download video for row {row_num}. Skipping...")
            continue

        audio_success = extract_audio(temp_video_path, output_audio_path)

        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            print(f"Cleaned up temporary video file: {temp_video_path}")

        if audio_success:
            try:
                update_row_status(sheet_id, row_num, "Completed")
                print(f"Successfully processed interview for Row {row_num}!\n")
            except Exception as e:
                print(f"Audio extracted, but failed to update status in Google Sheet: {e}\n")
        else:
            print(f"Audio extraction failed for row {row_num}.\n")

    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
        os.rmdir(temp_dir)

    print("Pipeline execution completed!")

if __name__ == "__main__":
    main()