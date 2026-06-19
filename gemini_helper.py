import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class QAItem(BaseModel):
    question_number: int = Field(
        description="The sequential number of the question, strating from 1."
    )
    question_text: str = Field(
        description="The question asked by the interviewer in the recording."
    )
    answer_text: str=Field(
        description="The corresponding answer given by the interviewee."
    )

class InterviewExtraction(BaseModel):
    qa_list: list[QAItem] = Field(
        description="A list of all questions and their corresponding answers extracted from the recording."
    )

def extract_qa_from_audio(audio_path: str) -> list[QAItem]:
    api_key=os.getenv("Gemini_API_KEY")
    if not api_key:
        raise ValueError("Please set Gemini_API_KEY in your .env file.")
    
    if not os.path.exists(audio_path):
        raise ValueError(f"Audio file not found: {audio_path}")
    
    client = genai.Client(api_key=api_key)
    print(f"Uploading '{audio_path}' to Gemini...")
    uploaded_file = client.files.upload(file=audio_path)
    print(f"Upload completed! File URI: {uploaded_file.uri}")
    
    try:
        print("Analyzing audio and extracting questions/answers. Please wait...")

        prompt = (
            "Analyze this interview recording carefully. Listen to the exchange between "
            "the interviewer and the interviewee. Extract all questions asked by the "
            "interviewer, and match each question with the answer given by the interviewee."
        )

        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InterviewExtraction,
                temperature=0.2,
            ),
        )

        extraction: InterviewExtraction = response.parsed
        print(f"Successfully extracted {len(extraction.qa_list)} Q&A pairs!")

        return extraction.qa_list
    
    finally:
        print("Cleaning up file from Google gemini storage...")
        client.files.delete(name=uploaded_file.name)
        print("cleanup completed")

if __name__ == "__main__":
    print("Testing Gemini Helper module...")
    try:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            print("Status: GEMINI_API_KEY is missing from .env (we will configure this later).")
        else:
            print("Status: GEMINI_API_KEY found! Helper ready for execution.")
    except Exception as e:
        print(f"Test failed: {e}")