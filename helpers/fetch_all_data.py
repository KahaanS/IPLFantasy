#!/usr/bin/env python3
"""
Master script to fetch all data needed for fantasy cricket points calculation.
Runs scorecards and player info fetchers in sequence.
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """Run a Python script and return success status."""
    print(f"\n{'='*70}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print(f"\n✓ {description} completed successfully!")
            return True
        else:
            print(f"\n✗ {description} failed with return code {result.returncode}")
            return False
    
    except FileNotFoundError:
        print(f"\n✗ Error: {script_name} not found")
        return False
    except Exception as e:
        print(f"\n✗ Error running {script_name}: {e}")
        return False

def main():
    """Main function to run all data fetchers."""
    print("\n" + "="*70)
    print("IPL FANTASY CRICKET DATA FETCHER")
    print("="*70)
    print("\nThis script will fetch:")
    print("  1. Match scorecards for all completed matches")
    print("  2. Player information for all players in those matches")
    print("\nData will be stored in:")
    print("  - scorecards/ folder (match details)")
    print("  - players_info/ folder (player stats)")
    print("\n" + "="*70)
    
    input("Press Enter to start fetching data...")
    
    all_success = True
    
    # Step 1: Fetch scorecards
    success = run_script(
        "fetch_scorecards.py",
        "Step 1: Fetching Match Scorecards"
    )
    all_success = all_success and success
    
    if not success:
        print("\nWarning: Scorecard fetching had issues. Continuing anyway...")
    
    # Step 2: Fetch player info
    success = run_script(
        "fetch_players_info.py",
        "Step 2: Fetching Player Information"
    )
    all_success = all_success and success
    
    # Final summary
    print("\n" + "="*70)
    if all_success:
        print("✓ ALL DATA FETCHING COMPLETED SUCCESSFULLY!")
    else:
        print("⚠ SOME STEPS HAD ISSUES - CHECK OUTPUT ABOVE")
    print("="*70)
    
    print("\nYour data is ready:")
    print("  📁 scorecards/     - Contains match scorecards")
    print("  📁 players_info/   - Contains player statistics")
    
    print("\n" + "="*70 + "\n")
    
    sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    main()
