import requests
import json
import os
from pathlib import Path
from collections import defaultdict
from .api_helpers import load_config_yaml
import yaml

# Configuration
SCORECARDS_FOLDER = "scorecards"
PLAYERS_FOLDER = "players_info"
SERIES_INFO_FILE = "seriesinfo.json"

# Create players_info folder if it doesn't exist
Path(PLAYERS_FOLDER).mkdir(exist_ok=True)
    
# def load_api_key():
#     """Load API key from series info file."""
#     with open(SERIES_INFO_FILE, 'r') as f:
#         data = json.load(f)
#     return data.get('apikey')

def get_scorecard_files():
    """Get list of all scorecard JSON files."""
    try:
        return [f for f in os.listdir(SCORECARDS_FOLDER) if f.endswith('.json')]
    except FileNotFoundError:
        print(f"Error: {SCORECARDS_FOLDER} folder not found.")
        return []

def extract_player_ids_from_scorecard(scorecard_path):
    """Extract all unique player IDs from a scorecard."""
    player_ids = {}  # {player_id: player_name}
    
    try:
        with open(scorecard_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {scorecard_path}: {e}")
        return player_ids
    
    scorecard_list = data.get('data', {}).get('scorecard', [])
    
    for inning in scorecard_list:
        # Extract batting players
        batting = inning.get('batting', [])
        for batter in batting:
            batsman = batter.get('batsman', {})
            player_id = batsman.get('id')
            player_name = batsman.get('name')
            if player_id and player_name:
                player_ids[player_id] = player_name
        
        # Extract bowling players
        bowling = inning.get('bowling', [])
        for bowler in bowling:
            bowler_info = bowler.get('bowler', {})
            player_id = bowler_info.get('id')
            player_name = bowler_info.get('name')
            if player_id and player_name:
                player_ids[player_id] = player_name
        
        # Extract fielding players
        catching = inning.get('catching', [])
        for fielder in catching:
            catcher_info = fielder.get('catcher', {})
            player_id = catcher_info.get('id')
            player_name = catcher_info.get('name')
            if player_id and player_name:
                player_ids[player_id] = player_name
    
    return player_ids

def player_info_exists(player_id):
    """Check if player info already exists locally."""
    for file in os.listdir(PLAYERS_FOLDER):
        if player_id in file:
            return True
    return False

def get_player_filename(player_id, player_name):
    """Generate a filename for the player info."""
    safe_name = "".join(c for c in player_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
    return f"{safe_name}_{player_id}.json"

def fetch_player_info(apikey, player_id):
    """Fetch player info from API."""
    try:
        url = f"https://api.cricapi.com/v1/players_info?apikey={apikey}&offset=0&id={player_id}"
        print(f"    Fetching player info from API...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"    Error fetching player info: {e}")
        return None

def save_player_info(player_data, filename):
    """Save player info to JSON file."""
    try:
        filepath = os.path.join(PLAYERS_FOLDER, filename)
        with open(filepath, 'w') as f:
            json.dump(player_data, f, indent=2)
        return filepath
    except Exception as e:
        print(f"    Error saving player info: {e}")
        return None

def main():
    """Main function to fetch player info from scorecards."""
    print(f"Loading API key from {SERIES_INFO_FILE}...")
    config = load_config_yaml()
    apikey = config.get('API_KEY')
    
    if not apikey:
        print("Error: API key not found in series data.")
        return
    
    print(f"Getting scorecard files from {SCORECARDS_FOLDER}...")
    scorecard_files = get_scorecard_files()
    
    if not scorecard_files:
        print("No scorecard files found.")
        return
    
    print(f"Found {len(scorecard_files)} scorecard files.\n")
    
    # Collect all unique players from all scorecards
    all_players = {}  # {player_id: player_name}
    
    for scorecard_file in scorecard_files:
        scorecard_path = os.path.join(SCORECARDS_FOLDER, scorecard_file)
        players = extract_player_ids_from_scorecard(scorecard_path)
        all_players.update(players)
    
    print(f"Found {len(all_players)} unique players across all scorecards.\n")
    
    # Process each unique player
    fetched_players = 0
    already_exist = 0
    failed_downloads = 0
    
    for idx, (player_id, player_name) in enumerate(all_players.items(), 1):
        print(f"[{idx}/{len(all_players)}] {player_name}")
        print(f"      Player ID: {player_id}")
        
        # Check if player info already exists
        if player_info_exists(player_id):
            print(f"      ✓ Player info already exists locally")
            already_exist += 1
            continue
        
        # Fetch player info from API
        player_data = fetch_player_info(apikey, player_id)
        
        if player_data is None:
            print(f"      ✗ Failed to fetch player info")
            failed_downloads += 1
            continue
        
        # Save player info
        filename = get_player_filename(player_id, player_name)
        filepath = save_player_info(player_data, filename)
        
        if filepath:
            print(f"      ✓ Player info saved: {filename}")
            fetched_players += 1
        else:
            print(f"      ✗ Failed to save player info")
            failed_downloads += 1
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total unique players found: {len(all_players)}")
    print(f"Player info already existed: {already_exist}")
    print(f"New player info downloaded: {fetched_players}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Players folder: {PLAYERS_FOLDER}")
    print("="*70)

if __name__ == "__main__":
    main()
