import io
import pickle
import sys
import os.path
from googleapiclient.discovery import *
from google_auth_oauthlib.flow import *
from google.auth.transport.requests import *
from googleapiclient.http import *

class Gdriver:

    def __init__(self):
        self.service = self.connect()

    def connect(self):
        """ Shows basic usage of the Drive v3 API.
            Prints the names and ids of the first 10 files the user has access to.
        """
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/drive',
                  'https://www.googleapis.com/auth/spreadsheets']

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.

        # getting correct path of the application
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
            path = os.path.dirname(sys.executable)
            parent = os.path.abspath(os.path.join(path, os.pardir))
        else:
            app_path = os.getcwd()

        try:
            if os.path.exists(parent + '/Resources/token.pickle'):
                with open(parent + '/Resources/token.pickle', 'rb') as token:
                    creds = pickle.load(token)
        except:
            if os.path.exists(app_path + '/token.pickle'):
                with open(app_path + '/token.pickle', 'rb') as token:
                    creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(app_path + '/credentials.json', SCOPES)

                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            try:
                with open(parent + '/Resources/token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            except:
                with open(app_path + '/token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

        service = build('drive', 'v3', credentials=creds)
        return service

    def fetch_file(self, filename):
        results = self.service.files().list(
                        q=f"name contains '{filename}'",
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType)').execute()

        # Assumes only one with that the input name
        file_id = results.get('files', [])[0]['id']
        file_type = results.get('files', [])[0]['mimeType']

        # Check file type and send request appropriately
        if 'application/vnd.google-apps' in file_type:
            # Google drive file types
            google_filetype = file_type.split(".")[-1]
            if google_filetype == "spreadsheet":
                download_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif google_filetype == "document":
                download_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            request = self.service.files().export_media(fileId=file_id, mimeType=download_type)
            fh = io.BytesIO()
        # Microsoft office types
        elif "wordprocessing" in file_type or "spreadsheet" in file_type:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
        # csv
        else:
            request = self.service.files().get_media(fileId=file_id)
            if getattr(sys, 'frozen', False):
                path = os.path.dirname(sys.executable)
                parent = os.path.abspath(os.path.join(path, os.pardir))
            else:
                app_path = os.getcwd()

            try:
                path = parent + "/Resources/file.csv"
            except:
                path = app_path + "/file.csv"
            fh = io.FileIO(path, "wb")

        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
           # print("Download %d%%." % int(status.progress() * 100))
        return fh, file_id

    def push_file(self, filename, file_path, **kwargs):
        """ Upload to google drive, update existing file
        """
        file_metadata = {"name": filename}

        media = MediaFileUpload(file_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Update file if file id is given
        if kwargs.get("fileId") != None:
            f = self.service.files().update(fileId=kwargs.get("fileId"),
                                            body=file_metadata,
                                            media_body=media,
                                            fields="id").execute()
        else:
            f = self.service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields="id").execute()
