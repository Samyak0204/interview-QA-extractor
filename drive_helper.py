import os
import re
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

def extract_file(url):
    match=re.search(r'/d/([a-zA-Z0-9_-]+)',url)
    if match:
        return match.group(1)
    
    match = re.search(r'id=([a-zA-Z0-9_-]+)',url)
    if match:
        return match.group(1)
    
    return url

def get_drive_service():
    service_acc_file=os.getenv("SERVICE_ACCOUNT_FILE","service_account.json")
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
    creds = service_account.Credentials.from_service_account_file(service_acc_file, scopes=scopes)

    service= build("drive", "v3", credentials=creds)
    return service

def download_video(file_id, output_path):
    service = get_drive_service()
    try:
        file_metadata=service.files().get(fileId=file_id, fields="name,size").execute()
        file_name = file_metadata.get("name")
        file_size = int(file_metadata.get("size",0))
        print(f"Downloading file: {file_name} ({file_size / (1024*1024):.2f} MB)...")
    except Exception as e:
        print(f"Error fetching file metadata: {e}")
        return False
    
    request = service.files().get_media(fileId=file_id)

    with io.FileIO(output_path, "wb") as f:
        downloader = MediaIoBaseDownload(f,request, chunksize=1024*1024)
        done = False
        with tqdm(total=file_size, unit="B", unit_scale=True, desc=file_name) as pbar:
            last_downloaded = 0
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    current_downloaded = int(status.resumable_progress)
                    pbar.update(current_downloaded - last_downloaded)
                    last_downloaded = current_downloaded
    
    print(f"Download complete. Saved to: {output_path}")
    return True

if __name__ == "__main__":
    test_link="https://drive.google.com/file/d/1aTp8aefcNHioggiqDqkzdXWSYRu9dfu_/view?usp=drive_link"
    file_id=extract_file(test_link)
    output_path="test.mp4"
    download_video(file_id, output_path)