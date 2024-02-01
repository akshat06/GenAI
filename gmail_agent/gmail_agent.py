import os
import pickle
import base64
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
from google.oauth2.credentials import Credentials


def getEmails():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If credentials are not available or are invalid, ask the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the access token in token.pickle file for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Connect to the Gmail API
    service = build('gmail', 'v1', credentials=creds)

    # request a list of all the messages
    result = service.users().messages().list(userId='me').execute()

    # We can also pass maxResults to get any number of emails. Like this:
    result = service.users().messages().list(maxResults=2, userId='me').execute()
    messages = result.get('messages')

    # Initialize an empty list to store the emails
    emails = []

    # iterate through all the messages
    for msg in messages:
        # Get the message from its id
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()

        # Use try-except to avoid any Errors
        try:
            # Get value of 'payload' from dictionary 'txt'
            payload = txt['payload']
            headers = payload['headers']

            # Look for Subject and Sender Email in the headers
            for d in headers:
                if d['name'] == 'Subject':
                    subject = d['value']
                if d['name'] == 'From':
                    sender = d['value']

            # The Body of the message is in Encrypted format. So, we have to decode it.
            # Get the data and decode it with base 64 decoder.
            parts = payload.get('parts')[0]
            data = parts['body']['data']
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)

            # Now, the data obtained is in lxml. So, we will parse
            # it with BeautifulSoup library
            soup = BeautifulSoup(decoded_data , "lxml")
            body = soup.body()

            # Create a dictionary for the email
            email_dict = {
                'sender': sender,
                'subject': subject,
                'body': body
            }

            # Append the dictionary to the list of emails
            emails.append(email_dict)

            # Printing the subject, sender's email and message
            print("Subject: ", subject)
            print("From: ", sender)
            print("Message: ", body)
            print('\n')
        except:
            pass

    return emails



def fetch_last_n_emails(n):
    # Set up the Gmail API
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    CLIENT_SECRET_FILE = 'credentials.json'  # Replace with your client secret file
    TOKEN_PICKLE_FILE = 'token.json'

    # Set up credentials
    creds = None

    if os.path.exists(TOKEN_PICKLE_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_PICKLE_FILE)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PICKLE_FILE, 'w') as token:
            token.write(creds.to_json())

    # Create the Gmail API service
    service = build(API_NAME, API_VERSION, credentials=creds)

    # Get the last n emails
    results = service.users().messages().list(userId='me', maxResults=n).execute()
    messages = results.get('messages', [])

    # List to store JSON-formatted email information
    email_list = []

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        sender = [header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'][0]
        subject = [header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'][0]
        body = msg['snippet']

        # Create JSON and append to the list
        email_info = {'sender': sender, 'subject': subject, 'body': body}
        email_list.append(email_info)

    return email_list


