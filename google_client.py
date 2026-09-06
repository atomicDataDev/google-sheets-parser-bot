"""
Google Sheets client module.

Provides authenticated access to Google Drive API for retrieving spreadsheet
metadata and exporting documents as PDF.
"""
import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from config import GOOGLE_CREDS_DICT


class GoogleSheetsClient:
    """
    Client for interacting with Google Drive API using a service account.

    Handles OAuth2 token refresh automatically before each request.
    """

    SCOPES: list[str] = ["https://www.googleapis.com/auth/drive.readonly"]

    def __init__(self) -> None:
        """
        Initialize the client by loading service account credentials.
        """
        self.credentials = service_account.Credentials.from_service_account_info(
            GOOGLE_CREDS_DICT, scopes=self.SCOPES
        )

    def _get_access_token(self) -> str:
        """
        Return a valid OAuth2 access token, refreshing it if necessary.

        :return: A valid Bearer token string.
        :rtype: str
        """
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def get_modified_time(self, spreadsheet_id: str) -> str:
        """
        Fetch the last modification timestamp of a spreadsheet from Google Drive.

        Makes a lightweight metadata-only request to avoid downloading the full
        document on every polling cycle.

        :param spreadsheet_id: The Google Spreadsheet ID from its URL.
        :type spreadsheet_id: str
        :return: ISO 8601 timestamp string, or ``'unknown'`` on missing field.
        :rtype: str
        :raises requests.HTTPError: If the Drive API returns a non-2xx response.
        """
        url = (
            f"https://www.googleapis.com/drive/v3/files/{spreadsheet_id}"
            "?fields=modifiedTime"
        )
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}

        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json().get("modifiedTime", "unknown")

    def download_pdf(self, spreadsheet_id: str) -> str:
        """
        Export and download a spreadsheet as a PDF file.

        Streams the response in chunks to avoid loading the entire document
        into memory at once.

        :param spreadsheet_id: The Google Spreadsheet ID from its URL.
        :type spreadsheet_id: str
        :return: Local file path to the downloaded PDF.
        :rtype: str
        :raises requests.HTTPError: If the export request returns a non-2xx response.
        """
        url = (
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export"
            "?format=pdf&portrait=false&fitw=true"
        )
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}

        pdf_path = "temp_sheet.pdf"
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(pdf_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return pdf_path
