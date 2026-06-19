import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def get_sheets_service():
    service_acc_file=os.getenv("SERVICE_ACCOUNT_FILE","service_account.json")
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(service_acc_file, scopes=scopes)

    service= build("sheets", "v4", credentials=creds)
    return service

def read_sheets(sheet_id, range_name):
    service=get_sheets_service()
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    rows = result.get("values", [])

    if not rows:
        print("No data found.")
        return []
    
    headers = [h.strip() for h in rows[0]]
    data=[]

    for i,row in enumerate(rows[1:],start=2):
        while len(row) < len(headers):
            row.append("")

        row_dict={headers[col_idx]: row[col_idx] for col_idx in range(len(headers))}
        row_dict["row_num"] = i
        data.append(row_dict)

    return data

def update_row_status(sheet_id, row_num, status_value):
    service=get_sheets_service()

    range_name = f"Sheet1!D{row_num}"

    body = {
        "values": [[status_value]]
    }

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

    print(f"Row {row_num} status updated to '{status_value}' in Google Sheets.")

def ensure_worksheets_exist(sheet_id):
    service=get_sheets_service()
    sheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    
    existing_sheets = [s['properties']['title'] for s in sheet.get('sheets', [])]

    required_sheets = {
        "Questions": ["Interviewer_ID","Interviewee_ID","Question_ID","Question_text"],
        "Answers": ["Interviewer_ID","Interviewee_ID","Question_ID","Answer_text"]
    }

    for title, headers in required_sheets.items():
        if title not in existing_sheets:
            print(f"Worksheet '{title}' not found. Creating it...")

            add_request = {
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": title
                            }
                        }
                    }
                ]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body=add_request
            ).execute()

            body = {"values": [headers]}
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{title}!A1:D1",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            print(f"Worksheet '{title}' created with headers.")

def append_qa_to_sheets(sheet_id, interviewer_id, interviewee_id, qa_list):
    service=get_sheets_service()
    ensure_worksheets_exist(sheet_id)

    questions_rows=[]
    answers_rows = []

    for item in qa_list:
        q_id = f"Q{item.question_number}"
        questions_rows.append([interviewer_id, interviewee_id, q_id, item.question_text])
        answers_rows.append([interviewer_id, interviewee_id, q_id, item.answer_text])

    if questions_rows:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Questions!A:D",
            valueInputOption="USER_ENTERED",
            body={"values": questions_rows}
        ).execute()
        print(f"Appended {len(questions_rows)} questions to Sheets.")

    if answers_rows:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Answers!A:D",
            valueInputOption="USER_ENTERED",
            body={"values": answers_rows}
        ).execute()
        print(f"Appended {len(answers_rows)} questions to Sheets.")


if __name__ == "__main__":
    sheet_id= os.getenv("SPREADSHEET_ID")
    range_name= os.getenv("SHEET_RANGE", "Sheet1!A1:D100")

    if not sheet_id or sheet_id=="your_google_spreadsheet_id_here":
        print("Error: Please set SPREADSHEET_ID in your .env file.")
    else:
        print(f"Testing sheets helper with Sheet ID: {sheet_id}...")
        try:
            # Let's test checking/creating worksheets
            print("Ensuring 'Questions' and 'Answers' sheets exist...")
            ensure_worksheets_exist(sheet_id)
            print("Sheets verification completed successfully!")
            
            # Let's verify we can read rows
            data = read_sheets(sheet_id, range_name)
            print(f"Found {len(data)} rows in main sheet.")
        except Exception as e:
            print(f"An error occurred during sheet tests: {e}")