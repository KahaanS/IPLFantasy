import json
import os
from pathlib import Path
from collections import defaultdict

# Configuration
SCORECARDS_FOLDER = "scorecards"
PLAYERS_FOLDER = "players_info"
OUTPUT_FOLDER = "player_points"

# Create output folder if it doesn't exist
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

def load_player_info(player_id):
    """Load player info from JSON file to get role."""
    for file in os.listdir(PLAYERS_FOLDER):
        if player_id in file:
            try:
                with open(os.path.join(PLAYERS_FOLDER, file), 'r') as f:
                    data = json.load(f)
                    return data.get('data', {})
            except json.JSONDecodeError:
                return None
    return None

def get_player_role(player_id):
    """Get player role from their info file."""
    player_info = load_player_info(player_id)
    if player_info:
        return player_info.get('role', 'Unknown')
    return 'Unknown'

def calculate_batting_points(batter, player_role):
    """Calculate batting points for a player using Dream11 T20 rules."""
    points = 0
    
    runs = batter.get('r', 0)
    fours = batter.get('4s', 0)
    sixes = batter.get('6s', 0)
    dismissal = batter.get('dismissal', '')
    
    # Run: +1 per run (Batting Points)
    points += runs * 1
    
    # Boundary Bonus: +4 per boundary (Batting Points)
    points += fours * 4
    
    # Six Bonus: +6 per six (Batting Points)
    points += sixes * 6
    
    # Milestone Run Bonus (hierarchical - only highest bracket awarded)
    # Century Bonus: +16 (Batting Points) - overrides all other milestone bonuses
    if runs >= 100:
        points += 16
    # 75 Run Bonus: +12 (Batting Points) - overrides 50 and 25 bonuses
    elif runs >= 75:
        points += 12
    # Half-Century Bonus: +8 for 50+ runs (Batting Points) - overrides 25 bonus
    elif runs >= 50:
        points += 8
    # 25 Run Bonus: +4 (Batting Points)
    elif runs >= 25:
        points += 4
    
    # Dismissal for a duck: -2 (Batter only) (Batting Points)
    # Only applies to players with Batsman role
    if runs == 0 and dismissal and player_role == 'Batsman':
        points -= 2
    
    return points

def calculate_bowling_points(bowler):
    """Calculate bowling points for a player using Dream11 T20 rules (excluding economy)."""
    points = 0
    
    overs = bowler.get('o', 0)
    runs = bowler.get('r', 0)
    wickets = bowler.get('w', 0)
    maidens = bowler.get('m', 0)
    
    # Dot Ball: +1 per dot ball (Bowling Points)
    # Note: We don't have individual dot ball data, so we skip this
    # as it requires ball-by-ball data not available in scorecard
    
    # Wicket (Excluding Run Out): +30 per wicket (Bowling Points)
    # Note: Scorecard doesn't separate run-outs from other wickets in bowling data
    # We apply this to all wickets as the data doesn't distinguish
    points += wickets * 30
    
    # Bonus (LBW/Bowled): +8 (Bowling Points)
    # Note: We don't have dismissal type per wicket in bowling data
    # This requires ball-by-ball data not available in scorecard
    
    # 3 Wicket Bonus: +4 for 3+ wickets (Bowling Points)
    if wickets >= 3:
        points += 4
    
    # 4 Wicket Bonus: +8 for 4+ wickets (Bowling Points)
    if wickets >= 4:
        points += 8
    
    # 5 Wicket Bonus: +12 for 5+ wickets (Bowling Points)
    if wickets >= 5:
        points += 12
    
    # Maiden Over: +12 per maiden over (Bowling Points)
    points += maidens * 12
    
    return points

def calculate_economy_rate_points(bowler):
    """Calculate economy rate bonus/penalty using Dream11 T20 rules."""
    points = 0
    
    overs = bowler.get('o', 0)
    runs = bowler.get('r', 0)
    
    # Calculate Economy Rate (minimum 2 overs)
    if overs >= 2:
        economy = runs / overs
        
        # Economy Rate Points (minimum 2 overs)
        if economy < 5:
            # Below 5 runs per over: +6
            points += 6
        elif economy < 6:
            # Between 5-5.99 runs per over: +4
            points += 4
        elif economy <= 7:
            # Between 6-7 runs per over: +2
            points += 2
        elif economy >= 10 and economy <= 11:
            # Between 10-11 runs per over: -2
            points -= 2
        elif economy > 11 and economy <= 12:
            # Between 11.01-12 runs per over: -4
            points -= 4
        elif economy > 12:
            # Above 12 runs per over: -6
            points -= 6
    
    return points

def calculate_fielding_points(fielder):
    """Calculate fielding points for a player using Dream11 T20 rules."""
    points = 0
    
    catches = fielder.get('catch', 0)
    stumpings = fielder.get('stumped', 0)
    runouts = fielder.get('runout', 0)
    
    # Catch: +8 per catch (Fielding Points)
    points += catches * 8
    
    # Stumping: +12 per stumping (Fielding Points)
    points += stumpings * 12
    
    # Run out (Direct hit): +12 (Fielding Points)
    # Run out (Not a direct hit): +6 (Fielding Points)
    # Note: Scorecard doesn't specify direct vs indirect
    # Apply default run-out points
    if runouts > 0:
        # We default to non-direct hit (conservative estimate)
        points += runouts * 6
    
    # 3 Catch Bonus: +4 for 3+ catches (Fielding Points)
    # Important: Only awarded once even if player has more catches
    if catches >= 3:
        points += 4
    
    return points

def calculate_strike_rate_points(batter, player_role):
    """Calculate strike rate bonus/penalty using Dream11 T20 rules."""
    points = 0
    
    balls = batter.get('b', 0)
    runs = batter.get('r', 0)
    
    # Strike Rate (Except Bowler) Points (minimum 10 balls)
    # Only apply to non-bowlers
    if balls >= 10 and player_role != 'Bowler':
        sr = (runs / balls) * 100
        
        # Above 170 runs per 100 balls: +6
        if sr > 170:
            points += 6
        # Between 150.01-170 runs per 100 balls: +4
        elif sr > 150.01:
            points += 4
        # Between 130-150 runs per 100 balls: +2
        elif sr >= 130:
            points += 2
        # Negative points only for 70 or below
        elif sr <= 70:
            # Between 60-70 runs per 100 balls: -2
            if sr >= 60:
                points -= 2
            # Between 50-59.99 runs per 100 balls: -4
            elif sr >= 50:
                points -= 4
            # Below 50 runs per 100 balls: -6
            else:
                points -= 6
    
    return points

def calculate_player_points(scorecard, player_id, player_name, role, all_innings):
    """Calculate total points for a player across all innings in a match."""
    points_breakdown = {
        'batting_points': 0,
        'sr_points': 0,
        'bowling_points': 0,
        'economy_points': 0,
        'fielding_points': 0,
        'lineup_bonus': 4,  # In announced lineups: +4 (Other Points)
        'total': 0
    }
    
    # Calculate points from all innings
    for inning_data in all_innings:
        # Calculate batting points
        batting_list = inning_data.get('batting', [])
        for batter in batting_list:
            if batter.get('batsman', {}).get('id') == player_id:
                batting_pts = calculate_batting_points(batter, role)
                points_breakdown['batting_points'] += batting_pts
                
                # Add strike rate points for batters
                sr_pts = calculate_strike_rate_points(batter, role)
                points_breakdown['sr_points'] += sr_pts
                break
        
        # Calculate bowling points
        bowling_list = inning_data.get('bowling', [])
        for bowler in bowling_list:
            if bowler.get('bowler', {}).get('id') == player_id:
                bowling_pts = calculate_bowling_points(bowler)
                points_breakdown['bowling_points'] += bowling_pts
                
                # Add economy rate points
                economy_pts = calculate_economy_rate_points(bowler)
                points_breakdown['economy_points'] += economy_pts
                break
        
        # Calculate fielding points
        catching_list = inning_data.get('catching', [])
        for fielder in catching_list:
            if fielder.get('catcher', {}).get('id') == player_id:
                fielding_pts = calculate_fielding_points(fielder)
                points_breakdown['fielding_points'] += fielding_pts
                break
    
    # Calculate total (lineup bonus added only once per match)
    points_breakdown['total'] = (
        points_breakdown['batting_points'] +
        points_breakdown['sr_points'] +
        points_breakdown['bowling_points'] +
        points_breakdown['economy_points'] +
        points_breakdown['fielding_points'] +
        points_breakdown['lineup_bonus']
    )
    
    return points_breakdown

def get_all_unique_players(scorecard):
    """Extract all unique players from a scorecard."""
    players = {}  # {player_id: player_name}
    
    for inning in scorecard.get('data', {}).get('scorecard', []):
        # From batting
        for batter in inning.get('batting', []):
            batsman = batter.get('batsman', {})
            player_id = batsman.get('id')
            player_name = batsman.get('name')
            if player_id and player_name:
                players[player_id] = player_name
        
        # From bowling
        for bowler in inning.get('bowling', []):
            bowler_info = bowler.get('bowler', {})
            player_id = bowler_info.get('id')
            player_name = bowler_info.get('name')
            if player_id and player_name:
                players[player_id] = player_name
        
        # From fielding
        for fielder in inning.get('catching', []):
            catcher = fielder.get('catcher', {})
            player_id = catcher.get('id')
            player_name = catcher.get('name')
            if player_id and player_name:
                players[player_id] = player_name
    
    return players

def process_scorecard(scorecard_path):
    """Process a single scorecard and calculate points for all players."""
    try:
        with open(scorecard_path, 'r') as f:
            scorecard = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {scorecard_path}: {e}")
        return None
    
    match_data = scorecard.get('data', {})
    match_id = match_data.get('id')
    match_name = match_data.get('name', 'Unknown Match')
    
    # Get all unique players
    all_players = get_all_unique_players(scorecard)
    
    # Get all innings for the match
    all_innings = match_data.get('scorecard', [])
    
    # Calculate points for each player
    player_points = {}
    
    for player_id, player_name in all_players.items():
        # Get player role
        role = get_player_role(player_id)
        
        # Calculate points across all innings (lineup bonus added only once)
        breakdown = calculate_player_points(
            scorecard, 
            player_id, 
            player_name,
            role,
            all_innings
        )
        
        player_points[player_id] = {
            'name': player_name,
            'role': role,
            'points': breakdown
        }
    
    return {
        'match_id': match_id,
        'match_name': match_name,
        'player_points': player_points
    }

def main():
    """Main function to process all scorecards and calculate points."""
    print("="*70)
    print("FANTASY CRICKET POINTS CALCULATOR")
    print("Using Dream11 T20 Rules")
    print("="*70 + "\n")
    
    # Get all scorecard files
    try:
        scorecard_files = [f for f in os.listdir(SCORECARDS_FOLDER) if f.endswith('.json')]
    except FileNotFoundError:
        print(f"Error: {SCORECARDS_FOLDER} folder not found.")
        return
    
    if not scorecard_files:
        print("No scorecard files found.")
        return
    
    print(f"Found {len(scorecard_files)} scorecard(s).\n")
    
    all_match_results = []
    
    for idx, scorecard_file in enumerate(scorecard_files, 1):
        print(f"[{idx}/{len(scorecard_files)}] Processing {scorecard_file}")
        
        scorecard_path = os.path.join(SCORECARDS_FOLDER, scorecard_file)
        result = process_scorecard(scorecard_path)
        
        if result:
            all_match_results.append(result)
            print(f"      ✓ Calculated points for {len(result['player_points'])} players")
        else:
            print(f"      ✗ Failed to process scorecard")
    
    # Save results
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print(f"{'='*70}\n")
    
    for match_result in all_match_results:
        match_id = match_result['match_id']
        match_name = match_result['match_name']
        player_points = match_result['player_points']
        
        # Create output filename
        safe_name = "".join(c for c in match_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]
        output_filename = f"{safe_name}_{match_id}.json"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Save to JSON
        try:
            with open(output_path, 'w') as f:
                json.dump({
                    'match_id': match_id,
                    'match_name': match_name,
                    'player_points': player_points
                }, f, indent=2)
            
            print(f"Match: {match_name}")
            print(f"  ✓ Saved: {output_filename}")
            
            # Create sorted rankings
            sorted_players = sorted(
                player_points.items(),
                key=lambda x: x[1]['points']['total'],
                reverse=True
            )
            
            print(f"  Top 5 Players by Fantasy Points:")
            for rank, (player_id, data) in enumerate(sorted_players[:5], 1):
                points = data['points']
                breakdown = (
                    f"Bat:{points['batting_points']}, "
                    f"SR:{points['sr_points']}, "
                    f"Bowl:{points['bowling_points']}, "
                    f"Eco:{points['economy_points']}, "
                    f"Field:{points['fielding_points']}, "
                    f"Bonus:{points['lineup_bonus']}"
                )
                print(f"    {rank}. {data['name']} ({data['role']}) - {points['total']} pts | {breakdown}")
            
            print()
        
        except Exception as e:
            print(f"Error saving results: {e}")
    
    # Print summary
    print(f"{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Scorecards processed: {len(scorecard_files)}")
    print(f"Total players analyzed: {sum(len(m['player_points']) for m in all_match_results)}")
    print(f"Results saved to: {OUTPUT_FOLDER}/")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
