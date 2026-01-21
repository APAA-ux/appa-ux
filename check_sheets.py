import os
from google_auth_oauthlib.flow import InstalledAppFlow

# The scope for reading Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def main():
    if not os.path.exists('client_secret.json'):
        print("ERROR: client_secret.json not found!")
        return

    # 1. Setup the flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    
    # We tell Google to redirect to localhost (which matches your Desktop Client setting)
    # This allows the login to succeed, even if the page doesn't load.
    flow.redirect_uri = 'http://localhost:8080'

    # 2. Generate the URL manually
    auth_url, _ = flow.authorization_url(prompt='consent')

    print("\n1. Click this link to log in:")
    print(auth_url)
    print("\n2. After you sign in, you will see a 'This site can't be reached' page.")
    print("3. Look at the URL bar of that broken page. It will look like:")
    print("   http://localhost:8080/?code=4/0Aea...&scope=...")
    print("4. COPY the entire value after 'code=' (between 'code=' and '&scope')")
    print("   OR just copy the WHOLE URL and paste it below.")

    # 3. Ask for the code
    code_input = input("\nPASTE THE CODE (or full URL) HERE: ").strip()

    # Clean up the input if the user pasted the full URL
    if "code=" in code_input:
        # Extract just the code part
        try:
            code_input = code_input.split('code=')[1].split('&')[0]
        except:
            pass # Trust the user input if split fails

    # 4. Exchange code for token
    try:
        flow.fetch_token(code=code_input)
        
        # Save the result
        with open('token.json', 'w') as token:
            token.write(flow.credentials.to_json())
        
        print("\nSUCCESS! Authentication complete.")
        print("token.json has been saved. You can now run your Streamlit app.")
        
    except Exception as e:
        print(f"\nError exchanging code: {e}")

if __name__ == '__main__':
    main()