"""
Master Orchestration Script for IPL Fantasy Cricket Points Pipeline

This script manages the complete pipeline by calling functions from other modules:
1. Download any new match scorecards
2. Download any new player information
3. Calculate fantasy points for new matches
4. Generate the summary CSV
5. Upload to Google Sheets

Run this script to keep your Google Sheet updated with the latest fantasy points!

Usage:
    python sync_fantasy_points.py
"""

import sys
import os
from datetime import datetime

# Import main functions from other modules
from helpers.fetch_scorecards import main as fetch_scorecards_main
from helpers.fetch_players_info import main as fetch_players_main
from helpers.calculate_fantasy_points import main as calculate_points_main
from helpers.generate_player_match_csv import generate_csv
from helpers.upload_to_google_sheets import main as upload_sheets_main
from helpers.api_helpers import load_config_yaml, cleanup_exposed_api_keys


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70 + "\n")


def print_section(title):
    """Print a section header."""
    print(f"\n{'─'*70}")
    print(f"➜ {title}")
    print(f"{'─'*70}\n")


def run_stage(stage_name, stage_func):
    """Run a pipeline stage and handle errors gracefully."""
    try:
        print_section(stage_name)
        stage_func()
        print(f"\n✓ {stage_name} completed")
        return True
    except KeyboardInterrupt:
        print(f"\n⚠️  {stage_name} interrupted by user")
        return False
    except Exception as e:
        print(f"\n⚠️  {stage_name} encountered an error: {e}")
        return False


def get_data_summary():
    """Get summary of current cached data."""
    summary = {
        'scorecards': 0,
        'players': 0,
        'player_points': 0,
        'csv_exists': os.path.exists('player_match_fantasy_points.csv')
    }
    
    if os.path.exists('scorecards'):
        summary['scorecards'] = len([f for f in os.listdir('scorecards') if f.endswith('.json')])
    
    if os.path.exists('players_info'):
        summary['players'] = len([f for f in os.listdir('players_info') if f.endswith('.json')])
    
    if os.path.exists('player_points'):
        summary['player_points'] = len([f for f in os.listdir('player_points') if f.endswith('.json')])
    
    return summary


def check_prerequisites():
    """Check if all required files exist."""
    print_section("Checking Prerequisites")
    
    required_files = {
        'seriesinfo.json': 'Series configuration',
        'fetch_scorecards.py': 'Scorecard fetcher',
        'fetch_players_info.py': 'Player info fetcher',
        'calculate_fantasy_points.py': 'Points calculator',
        'generate_player_match_csv.py': 'CSV generator',
        'upload_to_google_sheets.py': 'Google Sheets uploader'
    }
    
    optional_files = {
        'google_credentials.json': 'Google Sheets credentials (optional)'
    }
    
    missing_required = []
    
    # for file, description in required_files.items():
    #     if os.path.exists(file):
    #         print(f"✓ {description}: {file}")
    #     else:
    #         print(f"✗ {description}: {file}")
    #         missing_required.append(file)
    
    print()
    
    for file, description in optional_files.items():
        if os.path.exists(file):
            print(f"✓ {description}: {file}")
        else:
            print(f"ℹ️  {description}: {file} (not found - will skip Google Sheets upload)")
    
    if missing_required:
        print(f"\n✗ Missing required files: {', '.join(missing_required)}")
        return False
    
    print()
    return True


def main():
    """Main orchestration function."""
    
    print_header("IPL FANTASY CRICKET - SYNC PIPELINE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites check failed!")
        return False
    
    # Get initial state
    initial_state = get_data_summary()
    print_section("Current Data State")
    print(f"Scorecards cached: {initial_state['scorecards']}")
    print(f"Player profiles cached: {initial_state['players']}")
    print(f"Fantasy points calculated: {initial_state['player_points']}")
    print(f"Summary CSV exists: {'Yes' if initial_state['csv_exists'] else 'No'}")
    
    # Run pipeline stages
    all_success = True
    
    # Stage 1: Fetch new scorecards
    if not run_stage("Stage 1: Downloading New Scorecards", fetch_scorecards_main):
        all_success = False
    
    # Stage 2: Fetch new player information
    if not run_stage("Stage 2: Downloading New Player Data", fetch_players_main):
        all_success = False
    
    # Stage 3: Calculate fantasy points
    if not run_stage("Stage 3: Calculating Fantasy Points", calculate_points_main):
        all_success = False
    
    # Stage 4: Generate summary CSV
    if not run_stage("Stage 4: Generating Summary CSV", generate_csv):
        all_success = False
    
    # Stage 5: Upload to Google Sheets (optional)
    if os.path.exists('google_credentials.json'):
        if not run_stage("Stage 5: Uploading to Google Sheets", upload_sheets_main):
            print("\n⚠️  Note: CSV is still available locally at player_match_fantasy_points.csv")
            all_success = False
    else:
        print_section("Stage 5: Uploading to Google Sheets")
        print("ℹ️  Skipped: google_credentials.json not found")
        print("Your CSV is ready at: player_match_fantasy_points.csv")
    
    # Final summary
    print_header("SYNC COMPLETE")
    
    final_state = get_data_summary()
    
    print("Data Summary:")
    print(f"  Scorecards: {initial_state['scorecards']} → {final_state['scorecards']}")
    print(f"  Players: {initial_state['players']} → {final_state['players']}")
    print(f"  Fantasy Points: {initial_state['player_points']} → {final_state['player_points']}")
    print(f"  Summary CSV: {'✓ Generated' if final_state['csv_exists'] else '✗ Not found'}")
    
    if all_success:
        print(f"\n✓ Pipeline completed successfully!")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\n⚠️  Pipeline completed with warnings (see above for details)")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "="*70 + "\n")
    
    cleanup_exposed_api_keys('players_info')
    cleanup_exposed_api_keys('scorecards')
    cleanup_exposed_api_keys('player_points')
    
    print("✓ Cleaned up any exposed API keys from JSON files (if any)")
    
    return all_success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
