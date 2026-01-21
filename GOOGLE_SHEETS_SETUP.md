# Google Sheets Dashboard Setup Guide

## Overview
This dashboard automatically fetches and displays your sales data from Google Sheets with real-time updates.

## Prerequisites
- A Google Cloud Project
- A Google Sheet with sales data
- Service Account credentials (JSON file)

---

## Step 1: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet with your sales data
3. **Required columns** (at minimum):
   - `Name` - Salesperson name
   - `Product` - Product sold
   - `Amount` - Sale amount
   - `Quantity` - Units sold
   - `Price` - Unit price
   - `Region` - Sales region
   - `Status` - Order status (Pending, Completed, etc.)

**Example structure:**
```
| Date       | Name    | Product | Amount | Quantity | Price | Region | Status    |
|------------|---------|---------|--------|----------|-------|--------|-----------|
| 2026-01-20 | Alice   | Widget A| $1000  | 5        | $200  | West   | Completed |
| 2026-01-20 | Bob     | Widget B| $1500  | 3        | $500  | East   | Pending   |
```

4. Share the sheet (click Share → "Anyone with the link can view")
5. Copy the **Sheet ID** from the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

---

## Step 2: Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Search for "Google Sheets API"
   - Click "Enable"
4. Enable the Google Drive API:
   - Search for "Google Drive API"
   - Click "Enable"

---

## Step 3: Create Service Account

1. In Google Cloud Console, go to **Service Accounts** (under "APIs & Services")
2. Click **Create Service Account**
3. Fill in service account name and description
4. Click **Create and Continue**
5. Skip optional steps and click **Done**
6. Click on the created service account
7. Go to **Keys** tab
8. Click **Add Key** → **Create new key**
9. Choose **JSON**
10. Save the downloaded JSON file securely

---

## Step 4: Share Google Sheet with Service Account

1. Open the JSON key file and copy the **client_email** value
2. Open your Google Sheet
3. Click **Share** (top right)
4. Paste the client email
5. Give it **Editor** access
6. Click Share

---

## Step 5: Configure Streamlit Secrets

### Local Development

1. Create `.streamlit/secrets.toml` in your project:
   ```bash
   mkdir -p .streamlit
   touch .streamlit/secrets.toml
   ```

2. Open `.streamlit/secrets.toml` and add:
   ```toml
   google_sheet_id = "YOUR_SHEET_ID_HERE"
   
   [google_credentials]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "your-private-key-id"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "your-service-account@your-project.iam.gserviceaccount.com"
   client_id = "your-client-id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "your-cert-url"
   ```

3. Replace values from your JSON key file

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Deploy on [Streamlit Cloud](https://streamlit.io/cloud)
3. Go to app settings → **Secrets**
4. Paste your `.streamlit/secrets.toml` contents
5. Deploy

---

## Step 6: Run the Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will:
- ✅ Auto-load data from your Google Sheet
- ✅ Display real-time sales metrics
- ✅ Show charts and visualizations
- ✅ Refresh based on your selected interval

---

## Troubleshooting

### "Error loading Google Sheet"
- ✓ Check Google Sheet ID is correct
- ✓ Verify service account has access
- ✓ Ensure credentials are valid in secrets.toml

### "Could not find column"
- ✓ Verify column names match exactly (case-sensitive)
- ✓ Check Google Sheet has data in first row as headers

### No data showing
- ✓ Ensure Google Sheet is shared with service account email
- ✓ Check that data starts from row 2 (row 1 is headers)

---

## Auto-Update Features

The dashboard includes:
- **60-second auto-refresh** (default) - Polls Google Sheets every 60 seconds
- **30-second auto-refresh** - Update more frequently for live sales
- **Manual refresh** - Update only when needed

Select your preference in the dashboard.

---

## Next Steps

- Customize the KPI metrics to match your sales goals
- Add more columns to your Google Sheet for richer analysis
- Deploy to Streamlit Cloud for public access
- Add email alerts for milestones

Enjoy your automated sales dashboard! 📊
