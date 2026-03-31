import requests
import json
import os
from datetime import datetime
from pathlib import Path
from .api_helpers import load_config_yaml

# Configuration
SCORECARDS_FOLDER = "scorecards"
SERIES_INFO_FILE = "seriesinfo.json"

# Create scorecards folder if it doesn't exist
Path(SCORECARDS_FOLDER).mkdir(exist_ok=True)

def load_series_data():
    """Load the series information from JSON file."""
    with open(SERIES_INFO_FILE, 'r') as f:
        return json.load(f)

def get_scorecard_filename(match_id, match_name):
    """Generate a filename for the scorecard based on match ID and name."""
    # Create a safe filename from match name
    safe_name = "".join(c for c in match_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
    return f"{safe_name}_{match_id}.json"

def scorecard_exists(match_id):
    """Check if scorecard for a match already exists."""
    for file in os.listdir(SCORECARDS_FOLDER):
        if match_id in file:
            return True
    return False

def is_match_completed(date_time_gmt):
    """Check if match has already occurred based on GMT time."""
    try:
        match_time = datetime.fromisoformat(date_time_gmt.replace('Z', '+00:00'))
        current_time = datetime.now()
        # Note: You may want to adjust this to use UTC time instead of local time
        return match_time < current_time
    except ValueError as e:
        print(f"Error parsing date {date_time_gmt}: {e}")
        return False

def fetch_scorecard(apikey, match_id):
    """Fetch scorecard from API for a given match ID."""
    try:
        url = f"https://api.cricapi.com/v1/match_scorecard?apikey={apikey}&offset=0&id={match_id}"
        print(f"  Fetching scorecard from API...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching scorecard: {e}")
        return None

def save_scorecard(scorecard_data, filename):
    """Save scorecard data to JSON file."""
    try:
        filepath = os.path.join(SCORECARDS_FOLDER, filename)
        with open(filepath, 'w') as f:
            json.dump(scorecard_data, f, indent=2)
        return filepath
    except Exception as e:
        print(f"  Error saving scorecard: {e}")
        return None

def main():
    """Main function to process all matches and fetch scorecards."""
    print(f"Loading series data from {SERIES_INFO_FILE}...")
    series_data = load_series_data()
    
    config = load_config_yaml()
    apikey = config.get('API_KEY')
    if not apikey:
        print("Error: API key not found in config.")
        return
    
    match_list = series_data.get('data', {}).get('matchList', [])
    print(f"Found {len(match_list)} matches in series data.\n")
    
    completed_matches = 0
    fetched_scorecards = 0
    already_exist = 0
    
    for idx, match in enumerate(match_list, 1):
        match_id = match.get('id')
        match_name = match.get('name', 'Unknown')
        date_time_gmt = match.get('dateTimeGMT', '')
        
        print(f"[{idx}/{len(match_list)}] {match_name}")
        print(f"      Match ID: {match_id}")
        print(f"      Date/Time GMT: {date_time_gmt}")
        
        # Check if match has been completed
        if not is_match_completed(date_time_gmt):
            print(f"      Status: Not yet played (scheduled for future)")
            continue
        
        completed_matches += 1
        print(f"      Status: Match completed")
        
        # Check if scorecard already exists
        if scorecard_exists(match_id):
            print(f"      ✓ Scorecard already exists locally")
            already_exist += 1
            continue
        
        # Fetch scorecard from API
        scorecard_data = fetch_scorecard(apikey, match_id)
        
        if scorecard_data is None:
            print(f"      ✗ Failed to fetch scorecard")
            continue
        
        # Save scorecard
        filename = get_scorecard_filename(match_id, match_name)
        filepath = save_scorecard(scorecard_data, filename)
        
        if filepath:
            print(f"      ✓ Scorecard saved: {filename}")
            fetched_scorecards += 1
        else:
            print(f"      ✗ Failed to save scorecard")
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total matches processed: {len(match_list)}")
    print(f"Completed matches: {completed_matches}")
    print(f"Scorecard already existed: {already_exist}")
    print(f"New scorecards fetched: {fetched_scorecards}")
    print(f"Scorecards folder: {SCORECARDS_FOLDER}")
    print("="*70)

if __name__ == "__main__":
    main()
