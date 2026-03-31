import json
import os
import csv
from pathlib import Path
from datetime import datetime

# Configuration
POINTS_FOLDER = "player_points"
SCORECARDS_FOLDER = "scorecards"
OUTPUT_FILE = "player_match_fantasy_points.csv"

def load_match_dates():
    """Load match dates from scorecard files."""
    match_dates = {}
    
    if not os.path.exists(SCORECARDS_FOLDER):
        print(f"Warning: {SCORECARDS_FOLDER} folder not found. Dates may not be available.")
        return match_dates
    
    for scorecard_file in os.listdir(SCORECARDS_FOLDER):
        if not scorecard_file.endswith('.json'):
            continue
        
        try:
            with open(os.path.join(SCORECARDS_FOLDER, scorecard_file), 'r') as f:
                scorecard = json.load(f)
            
            match_data = scorecard.get('data', {})
            match_id = match_data.get('id')
            match_date_str = match_data.get('date')
            
            if match_id and match_date_str:
                # Parse the date (format: "2026-03-28")
                try:
                    match_date = datetime.strptime(match_date_str, "%Y-%m-%d")
                    match_dates[match_id] = match_date
                except ValueError:
                    pass
        except json.JSONDecodeError:
            pass
    
    return match_dates

def generate_csv():
    """Generate a CSV with player fantasy points for each match."""
    
    print("="*70)
    print("GENERATING PLAYER-MATCH FANTASY POINTS CSV")
    print("="*70 + "\n")
    
    # Check if points folder exists
    if not os.path.exists(POINTS_FOLDER):
        print(f"Error: {POINTS_FOLDER} folder not found.")
        print("Run calculate_fantasy_points.py first to generate player points.")
        return
    
    # Load match dates from scorecards
    print("Loading match dates from scorecards...")
    match_dates = load_match_dates()
    print(f"✓ Loaded dates for {len(match_dates)} matches\n")
    
    # Get all points files
    points_files = [f for f in os.listdir(POINTS_FOLDER) if f.endswith('.json')]
    
    if not points_files:
        print(f"No points files found in {POINTS_FOLDER}.")
        return
    
    print(f"Found {len(points_files)} match(es) with calculated points.\n")
    
    # Collect all player-match data
    player_match_data = []
    
    for points_file in points_files:
        try:
            with open(os.path.join(POINTS_FOLDER, points_file), 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing {points_file}: {e}")
            continue
        
        match_id = data.get('match_id')
        match_name = data.get('match_name')
        player_points = data.get('player_points', {})
        
        # Get match date if available
        match_date = match_dates.get(match_id, datetime.strptime("1970-01-01", "%Y-%m-%d"))
        
        # Extract each player's points for this match
        for player_id, player_data in player_points.items():
            player_name = player_data.get('name')
            player_role = player_data.get('role')
            points_breakdown = player_data.get('points', {})
            
            # Get individual point categories
            batting_points = points_breakdown.get('batting_points', 0)
            sr_points = points_breakdown.get('sr_points', 0)
            bowling_points = points_breakdown.get('bowling_points', 0)
            economy_points = points_breakdown.get('economy_points', 0)
            fielding_points = points_breakdown.get('fielding_points', 0)
            lineup_bonus = points_breakdown.get('lineup_bonus', 0)
            total_points = points_breakdown.get('total', 0)
            
            player_match_data.append({
                'player_id': player_id,
                'player_name': player_name,
                'player_role': player_role,
                'match_id': match_id,
                'match_name': match_name,
                'match_date': match_date,
                'batting_points': batting_points,
                'sr_points': sr_points,
                'bowling_points': bowling_points,
                'economy_points': economy_points,
                'fielding_points': fielding_points,
                'lineup_bonus': lineup_bonus,
                'total_points': total_points
            })
        
        print(f"Processed {match_name}: {len(player_points)} players")
    
    print(f"\nTotal player-match records: {len(player_match_data)}\n")
    
    # Sort by match date ascending (oldest first), then by player name
    player_match_data.sort(
        key=lambda x: (x['match_date'], x['player_name'])
    )
    
    # Write to CSV
    print(f"Writing to {OUTPUT_FILE}...\n")
    
    try:
        with open(OUTPUT_FILE, 'w', newline='') as csvfile:
            fieldnames = [
                'match_date',
                'player_name',
                'player_id',
                'player_role',
                'match_name',
                'match_id',
                'batting_points',
                'sr_points',
                'bowling_points',
                'economy_points',
                'fielding_points',
                'lineup_bonus',
                'total_points'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in player_match_data:
                writer.writerow({
                    'match_date': row['match_date'].strftime("%Y-%m-%d"),
                    'player_name': row['player_name'],
                    'player_id': row['player_id'],
                    'player_role': row['player_role'],
                    'match_name': row['match_name'],
                    'match_id': row['match_id'],
                    'batting_points': row['batting_points'],
                    'sr_points': row['sr_points'],
                    'bowling_points': row['bowling_points'],
                    'economy_points': row['economy_points'],
                    'fielding_points': row['fielding_points'],
                    'lineup_bonus': row['lineup_bonus'],
                    'total_points': row['total_points']
                })
        
        print(f"✓ CSV saved: {OUTPUT_FILE}")
        print(f"✓ Total records: {len(player_match_data)}")
        print(f"✓ Rows sorted by: Match Date (oldest first), Player Name (ascending)")
        
    except Exception as e:
        print(f"Error writing CSV: {e}")
        return
    
    # Print sample
    print(f"\nFirst 10 Player-Match Records (by Match Date):")
    print("-" * 120)
    
    sample_rows = [
        "Player Name, Role, Match, Batting, SR, Bowling, Eco, Field, Bonus, Total"
    ]
    
    for i, row in enumerate(player_match_data[:10], 1):
        sample_rows.append(
            f"{i}. {row['player_name']}, {row['player_role']}, "
            f"{row['match_name'][:40]}, "
            f"{row['batting_points']}, {row['sr_points']}, {row['bowling_points']}, "
            f"{row['economy_points']}, {row['fielding_points']}, "
            f"{row['lineup_bonus']}, {row['total_points']}"
        )
    
    for row in sample_rows:
        print(row)
    
    print("\n" + "="*70)
    print("CSV GENERATION COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    generate_csv()
