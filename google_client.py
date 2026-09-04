import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from config import GOOGLE_CREDS_DICT, TEMP_FILE_PATH

class GoogleSheetsClient:

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self):

        self.credentials = service_account.Credentials.from_service_account_info(
            GOOGLE_CREDS_DICT, scopes=self.SCOPES
        )

    def _get_access_token(self) -> str:

        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def download_to_file(self, spreadsheet_id: str) -> str:
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}

        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(TEMP_FILE_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return TEMP_FILE_PATH