import os
import json
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

@st.cache_resource
def get_creds():
    """Get or refresh Google Sheets API credentials"""
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Make sure client_secret.json exists
            if not os.path.exists('client_secret.json'):
                st.error("❌ client_secret.json not found. Please download it from Google Cloud Console.")
                st.stop()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            # Use secure local server method with proper host binding for Codespaces
            print("\n🔐 Starting authentication...")
            creds = flow.run_local_server(port=8080, host='0.0.0.0', open_browser=False)
            print("✓ Authentication successful!")
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

def get_sheets_service():
    """Get authorized Google Sheets service"""
    creds = get_creds()
    service = discovery.build('sheets', 'v4', credentials=creds)
    return service

def read_sheet(sheet_id, range_name):
    """
    Read data from a Google Sheet
    
    Args:
        sheet_id: The ID of the Google Sheet
        range_name: The range to read (e.g., 'August!A1:Z100')
    
    Returns:
        DataFrame with the sheet data
    """
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, 
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return None
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        st.error(f"Error reading from Google Sheets: {e}")
        return None
