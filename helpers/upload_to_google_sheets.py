"""
Google Sheets Integration for Fantasy Cricket Points

This script automatically uploads player-match fantasy points to a Google Sheet.

SETUP INSTRUCTIONS:
1. Install required library:
   pip install gspread google-auth-oauthlib google-auth-httplib2

2. Create a Google Cloud Project and Service Account:
   a. Go to https://console.cloud.google.com/
   b. Create a new project
   c. Enable Google Sheets API (APIs & Services > Library > Google Sheets API)
   d. Go to "Credentials" > Create Service Account
   e. In Service Account details, go to "Keys" tab
   f. Create a new JSON key
   g. Download and save as "google_credentials.json" in this folder

3. Create a Google Sheet:
   a. Go to https://sheets.google.com
   b. Create a new spreadsheet
   c. Get the SHEET_ID from the URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
   d. Share the sheet with the service account email (found in the JSON file)

4. Update the SHEET_ID and SHEET_NAME variables below

5. Run this script:
   python upload_to_google_sheets.py
"""

import json
import os
import csv
from pathlib import Path

from .api_helpers import load_config_yaml

# Try to import gspread
try:
    import gspread
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# Configuration
POINTS_FOLDER = "player_points"
CSV_FILE = "player_match_fantasy_points.csv"
CREDENTIALS_FILE = "google_credentials.json"

# IMPORTANT: Update these with your Google Sheet details
SHEET_NAME = "ScoreSheet"     # Name of the worksheet tab

# Scopes required for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def check_setup():
    """Check if all required files and configuration are present."""
    if not GSPREAD_AVAILABLE:
        print("Error: Required libraries not installed.")
        print("Install them with: pip install gspread google-auth-oauthlib google-auth-httplib2")
        return False
    
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: {CREDENTIALS_FILE} not found.")
        print("\nSetup Steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable Google Sheets API")
        print("4. Create a Service Account and download JSON key")
        print("5. Save the JSON file as 'google_credentials.json' in this folder")
        print("6. Share your Google Sheet with the service account email")
        return False
    
    return True

def authenticate():
    """Authenticate with Google Sheets API using service account."""
    try:
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=SCOPES
        )
        return credentials
    except Exception as e:
        print(f"Error authenticating: {e}")
        return None

def get_service_account_email():
    """Get service account email from credentials file."""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds = json.load(f)
            return creds.get('client_email', 'Unknown')
    except:
        return None

def convert_row_to_proper_types(row, fieldnames):
    """Convert numeric string values to actual numbers."""
    # Define which columns should be numeric
    numeric_columns = {
        'batting_points',
        'sr_points',
        'bowling_points',
        'economy_points',
        'fielding_points',
        'lineup_bonus',
        'total_points'
    }
    
    converted_row = []
    for field in fieldnames:
        value = row.get(field, '')
        
        # Convert numeric columns to float
        if field in numeric_columns and value != '':
            try:
                converted_row.append(float(value))
            except (ValueError, TypeError):
                converted_row.append(value)
        else:
            converted_row.append(value)
    
    return converted_row

def load_csv_data():
    """Load data from the CSV file."""
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.")
        print("Run 'python generate_player_match_csv.py' first to generate the CSV.")
        return None, None
    
    try:
        with open(CSV_FILE, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        if not rows:
            print("CSV file is empty.")
            return None, None
        
        # Get fieldnames (headers)
        fieldnames = reader.fieldnames
        
        return fieldnames, rows
    
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None, None

def upload_to_google_sheets():
    """Upload CSV data to Google Sheets."""
    
    print("="*70)
    print("UPLOADING FANTASY POINTS TO GOOGLE SHEETS")
    print("="*70 + "\n")
    
    config = load_config_yaml()
    SHEET_ID = config.get('SHEET_ID')
    
    # Check setup
    if not check_setup():
        return False
    
    print("Authenticating with Google Sheets API...")
    credentials = authenticate()
    if not credentials:
        return False
    
    print("✓ Authentication successful\n")
    
    # Load CSV data
    print("Loading CSV data...")
    fieldnames, rows = load_csv_data()
    if not rows:
        return False
    
    print(f"✓ Loaded {len(rows)} player-match records\n")
    
    # Connect to Google Sheets
    try:
        print("Connecting to Google Sheet...")
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Try to get existing worksheet or create new one
        try:
            worksheet = spreadsheet.worksheet(SHEET_NAME)
            print(f"✓ Found worksheet: {SHEET_NAME}")
        except gspread.exceptions.WorksheetNotFound:
            print(f"Creating new worksheet: {SHEET_NAME}")
            worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=len(rows)+1, cols=len(fieldnames))
            print(f"✓ Created worksheet: {SHEET_NAME}")
        
    except Exception as e:
        print(f"Error connecting to Google Sheet: {e}")
        print("\nMake sure:")
        print("1. SHEET_ID is correct (from URL)")
        print("2. The sheet is shared with the service account email")
        service_email = get_service_account_email()
        if service_email:
            print(f"   Service Account Email: {service_email}")
        print("3. google_credentials.json is valid")
        print("\nTo share the sheet:")
        print("1. Go to your Google Sheet")
        print("2. Click 'Share' (top right)")
        print(f"3. Add the service account email: {service_email}")
        print("4. Give it 'Editor' access")
        return False
    
    print(f"✓ Connected to Google Sheet ID: {SHEET_ID}\n")
    
    # Prepare data for upload
    print("Preparing data for upload...")
    data_to_upload = []
    
    # Add header row
    data_to_upload.append(list(fieldnames))
    
    # Add data rows with proper type conversion
    for row in rows:
        data_row = convert_row_to_proper_types(row, fieldnames)
        data_to_upload.append(data_row)
    
    print(f"✓ Prepared {len(data_to_upload)-1} records for upload\n")
    
    # Clear existing data and upload
    print("Uploading to Google Sheet...")
    try:
        # Clear all data first
        worksheet.clear()
        
        # Upload all data at once (more efficient than row by row)
        worksheet.update(data_to_upload)
        
        print(f"✓ Successfully uploaded {len(rows)} records to Google Sheet\n")
        
        # Format header row (optional)
        try:
            # Make header row bold
            format_range = gspread.utils.a1_range_to_grid_range(f"A1:{chr(64+len(fieldnames))}")
            worksheet.format(
                [format_range],
                {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                    "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                }
            )
            print("✓ Formatted header row\n")
        except Exception as e:
            print(f"Note: Could not format header row: {e}\n")
        
        return True
    
    except Exception as e:
        print(f"Error uploading to Google Sheet: {e}")
        if "403" in str(e) or "permission" in str(e).lower():
            print("\n⚠️  PERMISSION DENIED - This usually means:")
            print("The Google Sheet is NOT shared with the service account email.\n")
            service_email = get_service_account_email()
            if service_email:
                print(f"Service Account Email: {service_email}\n")
            print("TO FIX:")
            print("1. Go to your Google Sheet: https://docs.google.com/spreadsheets/d/{}/edit".format(SHEET_ID))
            print("2. Click the 'Share' button (top right)")
            print(f"3. Add this email: {service_email}")
            print("4. Set permission to 'Editor'")
            print("5. Click 'Share'")
            print("6. Then run this script again")
        return False

def main():
    """Main function."""
    success = upload_to_google_sheets()
    
    if success:
        print("✓ UPLOAD COMPLETE")
    else:
        print("✗ UPLOAD FAILED")

if __name__ == "__main__":
    main()
