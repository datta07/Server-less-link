import sys
import logging
import httplib2
from mimetypes import guess_type
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient.errors import ResumableUploadError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage


logging.basicConfig(level="ERROR")
token_file = sys.path[0] + '/auth_token.txt'
CLIENT_ID = '921616999170-sgmkjvmsh7sg3dr1ef6fg07t099nrqc0.apps.googleusercontent.com'
CLIENT_SECRET = '2v8IiIUBKKLiK_xCFiHce46a'
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive.file'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

def file_ops(file_path):
    mime_type = guess_type(file_path)[0]
    mime_type = mime_type if mime_type else 'text/plain'
    file_name = file_path.split('/')[-1]
    return file_name, mime_type


def create_token_file(token_file):
    flow = OAuth2WebServerFlow(
        CLIENT_ID,
        CLIENT_SECRET,
        OAUTH_SCOPE,
        redirect_uri=REDIRECT_URI
        )
    authorize_url = flow.step1_get_authorize_url()
    print('Go to the following link in your browser: ' + authorize_url)
    code = input('Enter verification code: ').strip()
    credentials = flow.step2_exchange(code)
    storage = Storage(token_file)
    storage.put(credentials)
    return storage


def authorize(token_file, storage):
    if storage is None:
        storage = Storage(token_file)
    credentials = storage.get()
    http = httplib2.Http()
    credentials.refresh(http)
    http = credentials.authorize(http)
    return http


def upload_file(file_path, file_name, mime_type):
    drive_service = build('drive', 'v2', http=http)
    media_body = MediaFileUpload(file_path,mimetype=mime_type,resumable=True)
    body = {
        'title': file_name,
        'description': 'backup',
        'mimeType': mime_type,
    }
    permissions = {
        'role': 'reader',
        'type': 'anyone',
        'value': None,
        'withLink': True
    }
    file = drive_service.files().insert(body=body, media_body=media_body).execute()
    drive_service.permissions().insert(fileId=file['id'], body=permissions).execute()
    file = drive_service.files().get(fileId=file['id']).execute()
    download_url = file.get('webContentLink')
    return download_url

if __name__ == '__main__':
    file_path = input("enter the file name:     ")
    try:
        with open(file_path) as f: 
            pass
    except IOError as e:
        print(e)
        sys.exit(1)

    try:
        with open(token_file) as f: pass
    except IOError:
        http = authorize(token_file, create_token_file(token_file))
    http = authorize(token_file, None)
    file_name, mime_type = file_ops(file_path)

    try:
        print(upload_file(file_path, file_name, mime_type))
    except ResumableUploadError as e:
        print("Error occured while first upload try:", e)
        print("Trying one more time.")
        print(upload_file(file_path, file_name, mime_type))