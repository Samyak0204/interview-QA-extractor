# interview-QA-extractor

A Python-based workflow integrating Google Drive, Sheets, and the Gemini API to download interview recordings, extract audio, and automatically generate and catalog structured Question & Answer pairs.

---

## 🚀 Features

- **FastAPI Web Dashboard:** Serve a local web interface featuring interactive statistics (Total, Completed, Pending rows) and a details table.
- **Live Streaming Logs:** Real-time console progress streamed directly to a simulated browser terminal using Server-Sent Events (SSE).
- **Metadata Sync:** Reads pending interviews and Google Drive video links directly from a Google Sheet.
- **Automated Downloads:** Uses a Google Service Account to download large video files securely from Google Drive.
- **Audio Extraction:** Programmatically extracts high-quality audio tracks using FFmpeg (`imageio-ffmpeg`).
- **AI Analysis & Speaker Diarization:** Natively leverages Gemini (`gemini-1.5-flash`) to perform speaker diarization and context mapping, automatically separating and matching the interviewer's questions with the interviewee's answers under a structured Pydantic JSON schema.
- **Result Export:** Automatically creates and appends questions and answers to dedicated sheets (`Questions` and `Answers`).
- **State Persistence:** Updates row status to `Completed` in the main sheet and cleans up temporary video files after processing.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Web Framework:** FastAPI, Uvicorn, Jinja2 Templates
- **AI/LLM:** Google GenAI SDK (`google-genai`), Pydantic
- **Media Processing:** FFmpeg (`imageio-ffmpeg`)
- **Cloud Integration:** Google Sheets API, Google Drive API

---

## 📊 Pipeline Architecture

```mermaid
graph TD
    A[Google Sheet: Pending Row] -->|Fetch metadata| B(main.py)
    B -->|Extract Link ID| C[Google Drive]
    C -->|Download Video| D[Local Temp Video]
    D -->|Extract Audio via FFmpeg| E[Local Audio File]
    E -->|Upload & Process| F[Gemini 1.5 Flash]
    F -->|Structured JSON Output| G[Pydantic Q&A Model]
    G -->|Append Questions & Answers| H[Google Sheet: 'Questions' / 'Answers']
    G -->|Update Row Status to Completed| I[Google Sheet: Main Row]
    B -->|Delete Temp Video| D
```

---

## ⚙️ Setup & Configuration

### Prerequisites
- Python 3.10+
- A Google Cloud Project with the Google Sheets and Google Drive APIs enabled.
- A Google Service Account credentials JSON file.
- A Gemini API Key.

### 1. Installation
Clone the repository, create a virtual environment, and install dependencies:
```bash
# Clone the repository
git clone https://github.com/Samyak0204/interview-QA-extractor.git
cd interview-QA-extractor

# Create a virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Cloud Setup
1. Download your service account credentials key file and place it in the root directory as `service_account.json`.
2. Share the Google Sheet and target Google Drive folder/files with your service account's client email (e.g., `your-service-account@your-project.iam.gserviceaccount.com`) giving them **Viewer** permission on Drive and **Editor** permission on Sheets.

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SPREADSHEET_ID=your_google_spreadsheet_id_here
SHEET_RANGE=Sheet1!A1:D100
SERVICE_ACCOUNT_FILE=service_account.json
```

---

## 📋 Google Sheet Structure

The main worksheet (defaulting to `Sheet1`) should have the following headers:
- `Interviewer_ID`
- `Interviewee_ID`
- `Link` (Google Drive video share link)
- `Status` (leave blank or set to something other than `Completed` for pending rows)

The pipeline will automatically create two new worksheets in the spreadsheet if they do not exist:
- **Questions:** Columns: `Interviewer_ID`, `Interviewee_ID`, `Question_ID`, `Question_text`
- **Answers:** Columns: `Interviewer_ID`, `Interviewee_ID`, `Question_ID`, `Answer_text`

---

## 🏃 Running the Application

1. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
2. Open your web browser and go to:
   ```
   http://127.0.0.1:8000
   ```
3. Click the **"Process Pending Interviews"** button to start the pipeline and watch live execution logs stream to the terminal panel.

---

## 🔮 Future Work & Roadmap

Planned enhancements to extend this pipeline's capabilities:

- **Containerization & Cloud Deployment:** Package the application into a Docker container to ensure system libraries (like FFmpeg) are correctly configured across cloud hosting environments (AWS, Render, etc.).
- **Error Handling & API Rate Limiting:** Implement retry logic using the `tenacity` library with exponential backoff to handle transient API rate limits (HTTP 429) and server errors (HTTP 500) gracefully.
- **Progress Bars:** Stream Google Drive download/processing status percentages to render visual progress bars in the browser dashboard.
- **Row Cancellation:** Add a "Cancel Run" button in the dashboard to safely terminate a running pipeline execution.
- **Google OAuth2 Login:** Transition from a single Google Service Account credentials key to OAuth2 login, allowing users to authenticate individually and grant the pipeline permissions to their own Drive and Sheets.

