import sqlite3
import json
import math
import re
import pandas as pd
from datetime import datetime

# ---------- Helper Functions ----------

def load_player(name, db_path="players.db"):
    """Load a player's record from SQLite as a dictionary."""
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM players WHERE name = ?"
    df = pd.read_sql_query(query, conn, params=(name,))
    conn.close()
    if df.empty:
        print(f"No data found for {name}")
        return None
    record = df.iloc[0].to_dict()
    print(f"\nLoaded record for {name}:")
    print(record)
    return record

def season_to_year(season_str):
    """
    Convert a season string like "2023-24" into its start year as an integer.
    Returns None if conversion fails or if season_str is 'CAREER'.
    """
    if not season_str or "CAREER" in season_str.upper():
        return None
    try:
        start_year = int(season_str.split("-")[0])
        return start_year
    except Exception:
        return None

def get_recent_seasons(nba_data):
    """
    Given nba_data (a list of season dictionaries), return a tuple:
      (previous_season, current_season)
    sorted by the season's start year (ignoring 'CAREER' rows).
    """
    valid_seasons = [s for s in nba_data if season_to_year(s.get("season", "")) is not None]
    print(f"\nValid seasons extracted: {[s.get('season') for s in valid_seasons]}")
    if not valid_seasons:
        return None, None
    valid_seasons.sort(key=lambda s: season_to_year(s.get("season", "")), reverse=True)
    current = valid_seasons[0]
    previous = valid_seasons[1] if len(valid_seasons) > 1 else None
    print(f"Current season: {current.get('season')}, Previous season: {previous.get('season') if previous else 'None'}")
    return previous, current

def convert_height_to_inches(height_str):
    """
    Convert a height string in the format "6-9" (feet-inches) into total inches.
    Returns None if conversion fails.
    """
    try:
        parts = height_str.split('-')
        if len(parts) == 2:
            feet = int(parts[0])
            inches = int(parts[1])
            return feet * 12 + inches
    except Exception as e:
        print("Error converting height:", e)
    return None

# New modified discount functions that also add a bonus for height above 6'10" (82 inches)
def modified_factor_for_ts(height_in_inches, threshold=82, discount_rate=0.2, min_factor=0.5, bonus_rate=0.1):
    """
    For players taller than threshold (82 inches), first discount TS% weight and then add a bonus.
    If height <= threshold, returns 1.0.
    """
    if height_in_inches <= threshold:
        return 1.0
    else:
        discount = 1 - (height_in_inches - threshold) * discount_rate
        discount = max(min_factor, discount)
        if height_in_inches > 84:
            bonus = (height_in_inches - threshold) * bonus_rate
        else:
            bonus = 0
        final_factor = discount + bonus
        return final_factor

def modified_factor_for_ortg(height_in_inches, threshold=82, discount_rate=0.5, min_factor=0.5, bonus_rate=0.1):
    """
    For players taller than threshold (82 inches), first discount ORTG weight and then add a bonus.
    If height <= threshold, returns 1.0.
    """
    if height_in_inches <= threshold:
        return 1.0
    else:
        discount = 1 - (height_in_inches - threshold) * discount_rate
        discount = max(min_factor, discount)
        if height_in_inches > 84:
            bonus = (height_in_inches - threshold) * bonus_rate
        else:
            bonus = 0
        final_factor = discount + bonus
        return final_factor

def compute_season_performance(season_stats, height_in_inches=None):
    """
    Compute a performance score for one season based on key features.
    A discount factor is applied if the season's games played ('gp') is low.
    For example, if gp < 25, the score is multiplied by (gp/25).
    For the 'ts%' and 'ortg' stats, if height_in_inches is provided, their weights are modified.
    (Feature weights below are illustrative – adjust them as needed.)
    For stats where a lower value is better (like drtg), a negative weight is applied.
    """
    feature_weights = {
        'ws': 1.1,       # overall win shares
        'per': 0.72,      # player efficiency rating
        'ortg': 1.0,      # offensive rating (more emphasis)
        'ppg': 2.7,       # scoring is key
        'fgm': 1.0,       # field goals made
        'trb': 0.42,      # rebounding (less weight for centers)
        'ts%': 0.15,      # true shooting percentage (modified by height)
        'stl': 0.4,       # steals
        'drtg': -1.2,     # lower defensive rating is better
        'ftm': 0.4,       # free throws made
        'blk': 0.68,      # blocks
        'usg%': 2.4,      # usage percentage
        'ows': 1.4,       # offensive win shares
        'dws': 1.1,       # defensive win shares
        '3p_pct': 0.55,   # three-point percentage
        'ast%': 0.55,     # assist percentage
        'min': 0.4,       # minutes played
    }
    
    # Extract games played ('gp') and calculate a discount factor if sample size is small.
    try:
        gp = float(season_stats.get("gp", 0))
    except Exception:
        gp = 0.0
    threshold_gp = 25.0  # adjust as needed
    discount_factor = min(1.0, gp / threshold_gp)
    
    score = 0.0
    for feature, weight in feature_weights.items():
        try:
            value = float(season_stats.get(feature, 0))
        except Exception:
            value = 0
        # For 'ts%', if height is available, use the modified factor
        if feature == 'ts%' and height_in_inches is not None:
            factor = modified_factor_for_ts(height_in_inches)
            weight *= factor
            print(f"Applying ts% modifier for height {height_in_inches} inches: new weight = {weight:.3f}")
        # For 'ortg', if height is available, use the modified factor
        if feature == 'ortg' and height_in_inches is not None:
            factor = modified_factor_for_ortg(height_in_inches)
            weight *= factor
            print(f"Applying ortg modifier for height {height_in_inches} inches: new weight = {weight:.3f}")
        score += weight * value
    score *= discount_factor
    print(f"Computed performance for season {season_stats.get('season')}: {score:.2f} (discount factor: {discount_factor:.2f} based on gp: {gp})")
    return score

def get_age_weights(age):
    """
    Return (previous_weight, current_weight) based on player's age.
    
    Age Ranges and corresponding weights:
      - 19-22: (0.25, 0.75)
      - 23-26: (0.40, 0.60)
      - 27-30: (0.50, 0.50)
      - 31-34: (0.45, 0.55)
      - 35-37: (0.325, 0.675)
      - 38+:   (0.10, 0.90)
    """
    if age < 19:
        weights = (0.25, 0.75)
    elif age <= 22:
        weights = (0.25, 0.75)
    elif age <= 26:
        weights = (0.40, 0.60)
    elif age <= 30:
        weights = (0.50, 0.50)
    elif age <= 34:
        weights = (0.45, 0.55)
    elif age <= 37:
        weights = (0.325, 0.675)
    else:
        weights = (0.10, 0.90)
    print(f"Age: {age} -> Age-based weights (previous, current): {weights}")
    return weights

def young_multiplier(age, current_rating):
    """
    For players aged 18 to 25, compute a bonus multiplier based on age and current rating.
    For players age 25 and over, the multiplier is 1.
    """
    if age < 27:
        rating_bonus = max(0, current_rating - 70)
        bonus = ((27 - age) / 7) * (rating_bonus / 30) * 2.6
        multiplier = 1 + bonus
    else:
        multiplier = 1.0
    print(f"Young multiplier for age {age} with current rating {current_rating}: {multiplier:.2f}")
    return multiplier

def compute_detailed_awards_bonus(awards_json, all_star_json, current_year):
    """
    Compute an awards bonus by parsing the awards and all-star JSON.
    Only awards from the past 5 years (relative to current_year) are considered.
    Award weights are defined below.
    
    Returns a tuple: (total_bonus, breakdown_dict)
    """
    award_weights = {
        "NBA Champion": {"recent": 3, "non_recent": 1, "recent_threshold": 3},
        "Michael Jordan Most Valuable Player": {"recent": 20, "non_recent": 4, "recent_threshold": 3},
        "Bill Russell NBA Finals MVP": {"recent": 16, "non_recent": 2, "recent_threshold": 3},
        "All-NBA First Team": {"recent": 18, "non_recent": 2, "recent_threshold": 3},
        "All-NBA Second Team": {"recent": 12, "non_recent": 1.5, "recent_threshold": 2},
        "All-NBA Third Team": {"recent": 10, "non_recent": 1, "recent_threshold": 2},
        "All-Defensive First Team": {"recent": 7, "non_recent": 1.5, "recent_threshold": 2},
        "All-Defensive Second Team": {"recent": 4.5, "non_recent": 1, "recent_threshold": 2},
        "All-Rookie First Team": {"recent": 2, "non_recent": 1, "recent_threshold": 2},
        "All-Rookie Second Team": {"recent": 1, "non_recent": 0.5, "recent_threshold": 2},
        "Rookie Of The Year": {"recent": 5, "non_recent": 2, "recent_threshold": 3},
        "Wilt Chamberlain Rookie Of The Year": {"recent": 7, "non_recent": 0.5, "recent_threshold": 3},
        "Player Of The Month": {"recent": 0.75, "non_recent": 0, "recent_threshold": 2},
        "Player Of The Week": {"recent": 0.4, "non_recent": 0, "recent_threshold": 2},
        "Eastern All-Star Fan Vote Selection": {"recent": 9, "non_recent": 1.5, "recent_threshold": 3},
        "Western All-Star Fan Vote Selection": {"recent": 9, "non_recent": 1.5, "recent_threshold": 3},
        "Kobe Bryant All-Star MVP": {"recent": 2, "non_recent": 2, "recent_threshold": 3},
        "Rising Stars Challenge Participant": {"recent": 0, "non_recent": 0, "recent_threshold": 3},
        "Skills Challenge Participant": {"recent": 0, "non_recent": 0.0, "recent_threshold": 3},
        "Skills Challenge Champion": {"recent": 0, "non_recent": 0, "recent_threshold": 3},
        "Hakeem Olajuwon Defensive Player Of The Year": {"recent": 7, "non_recent": 3, "recent_threshold": 3},
        "Kareem Abdul-Jabbar Scoring Champion": {"recent": 10, "non_recent": 3, "recent_threshold": 3},
        "Magic Johnson Assists Leader": {"recent": 5, "non_recent": 3, "recent_threshold": 3},
        "Dennis Rodman Rebounds Leader": {"recent": 5, "non_recent": 3, "recent_threshold": 3},
        "Mark Eaton Blocks Leader": {"recent": 5, "non_recent": 3, "recent_threshold": 3},
    }
    total_bonus = 0.0
    breakdown = {}

    def process_award(award_type, award_list):
        bonus = 0.0
        for item in award_list:
            # Extract any 4-digit years from the item
            years = re.findall(r'\d{4}', str(item))
            for y in years:
                try:
                    award_year = int(y)
                    age_diff = current_year - award_year
                    if age_diff > 5:
                        continue
                    thresh = award_weights.get(award_type, {}).get("recent_threshold", 3)
                    if age_diff <= thresh:
                        w = award_weights.get(award_type, {}).get("recent", 1)
                    else:
                        w = award_weights.get(award_type, {}).get("non_recent", 0.5)
                    bonus += w
                    breakdown.setdefault(award_type, []).append((award_year, w))
                except Exception:
                    continue
        return bonus

    try:
        awards_dict = json.loads(awards_json) if awards_json else {}
    except Exception:
        awards_dict = {}
    try:
        all_star_dict = json.loads(all_star_json) if all_star_json else {}
    except Exception:
        all_star_dict = {}

    combined_awards = awards_dict.copy()
    for key, val in all_star_dict.items():
        if key in combined_awards:
            if isinstance(combined_awards[key], list) and isinstance(val, list):
                combined_awards[key] += val
            else:
                combined_awards[key] = [combined_awards[key], val]
        else:
            combined_awards[key] = val

    for award_type, award_list in combined_awards.items():
        if not isinstance(award_list, list):
            award_list = [award_list]
        bonus = process_award(award_type, award_list)
        total_bonus += bonus

    print("\n--- Awards Bonus Breakdown ---")
    header = "{:<45} {:>15}".format("Award Type (Year, Weight)", "Bonus Points")
    print(header)
    print("-" * len(header))
    for award, entries in breakdown.items():
        for entry in entries:
            year, weight_val = entry
            print("{:<45} {:>15.2f}".format(f"{award} ({year})", weight_val))
    print("-" * len(header))
    print("{:<45} {:>15.2f}".format("Total Awards Bonus", total_bonus))
    return total_bonus, breakdown

def rating_factor(current_rating):
    """
    Convert current rating into a factor.
    For example, if ratings are typically in the 70-90 range, scale by dividing by 80.
    """
    try:
        rating = float(current_rating)
        factor = rating / 80.0
    except Exception:
        factor = 1.0
    print(f"\nCurrent season historical rating: {current_rating} -> Factor: {factor:.2f}")
    return factor

def get_current_rating_from_history(hist_ratings_json):
    """
    Extract the current rating from the historical ratings JSON.
    The season with the highest start year (e.g. "2024-2025") is used.
    """
    try:
        hist_ratings = json.loads(hist_ratings_json) if hist_ratings_json else {}
        if not hist_ratings:
            print("No historical ratings found, defaulting to 80.")
            return 80.0
        season_ratings = []
        for season_str, rating in hist_ratings.items():
            try:
                start_year = int(season_str.split("-")[0])
                season_ratings.append((start_year, float(rating)))
            except Exception as e:
                print(f"Error processing season {season_str}: {e}")
        if not season_ratings:
            print("No valid season ratings found, defaulting to 80.")
            return 80.0
        latest_rating = max(season_ratings, key=lambda x: x[0])[1]
        print(f"\nLatest historical rating determined: {latest_rating}")
        return latest_rating
    except Exception as e:
        print("Error parsing historical ratings:", e)
        return 80.0

def print_stats_table(stats):
    """
    Print a neat table of the calculation breakdown.
    """
    print("\n--- Calculation Breakdown ---")
    header = "{:<40} {:>15}".format("Component", "Value")
    print(header)
    print("-" * len(header))
    for key, value in stats.items():
        if isinstance(value, tuple):
            value = ", ".join(str(x) for x in value)
        elif isinstance(value, float):
            value = f"{value:.2f}"
        else:
            value = str(value)
        print("{:<40} {:>15}".format(key, value))
    print("-" * len(header))

def compute_injury_detractor(nba_data, threshold=60, seasons_to_consider=5, penalty_per_season=2.0):
    """
    Look at the last `seasons_to_consider` seasons (excluding the current season).
    Count how many of these seasons have 'gp' below the given threshold.
    If more than one season is low, apply a penalty for each extra season.
    """
    valid_seasons = [s for s in nba_data if season_to_year(s.get("season", "")) is not None]
    valid_seasons.sort(key=lambda s: season_to_year(s.get("season", "")), reverse=True)
    seasons_to_penalize = valid_seasons[1:seasons_to_consider+1] if len(valid_seasons) > 1 else []
    
    low_gp_count = 0
    for season in seasons_to_penalize:
        try:
            gp = float(season.get("gp", 0))
        except Exception:
            gp = 0.0
        if gp < threshold:
            low_gp_count += 1
    if low_gp_count > 1:
        return (low_gp_count - 1) * penalty_per_season
    return 0.0

def compute_age_penalty(age, threshold=33, penalty_per_year=2.2):
    """
    For players over the threshold age (default 33), apply a penalty for each year above.
    """
    if age > threshold:
        penalty = (age - threshold) * penalty_per_year
        print(f"Age penalty for age {age}: {penalty:.2f}")
        return penalty
    return 0.0

# ---------- AVN Calculation ----------

def compute_AVN(player_record):
    """
    Compute the Asset Value Number (AVN) for a player using:
      - Weighted performance score from the last two seasons,
      - Detailed awards bonus (from the past 5 years),
      - Current season historical 2K rating,
      - A young-age multiplier,
      - An injury detractor based on recent low-game seasons,
      - And an age penalty for players over 36.
    """
    print("\n=== Computing AVN ===")
    try:
        nba_data = json.loads(player_record.get("nba_data", "[]"))
    except Exception as e:
        print("Error parsing nba_data:", e)
        nba_data = []
    print(f"\nNBA Data: {nba_data}")
    
    previous_season, current_season = get_recent_seasons(nba_data)
    if current_season is None:
        print("No recent season data available. Returning AVN = 0")
        return 0

    # Convert player's height to inches (if available)
    height_str = player_record.get("height", "")
    height_in_inches = convert_height_to_inches(height_str) if height_str else None
    if height_in_inches:
        print(f"Player height {height_str} converted to {height_in_inches} inches.")
    else:
        print("No valid height found.")

    # Compute performance scores, passing height_in_inches for TS% and ORTG modifiers
    current_score = compute_season_performance(current_season, height_in_inches)
    previous_score = compute_season_performance(previous_season, height_in_inches) if previous_season else current_score

    try:
        age = float(player_record.get("current_age", 25))
    except Exception:
        age = 25
    weight_prev, weight_current = get_age_weights(age)
    base_perf = (weight_prev * previous_score) + (weight_current * current_score)
    print(f"\nBase performance score (weighted): {base_perf:.2f}")

    current_rating = get_current_rating_from_history(player_record.get("historical_ratings", "{}"))
    ym = young_multiplier(age, current_rating)
    
    # Awards bonus calculation
    current_year = season_to_year(current_season.get("season", "")) or datetime.now().year
    awards_bonus, awards_breakdown = compute_detailed_awards_bonus(
        player_record.get("nba_awards", "{}"),
        player_record.get("all_star_selections", "{}"),
        current_year
    )
    
    rating_mult = rating_factor(current_rating)
    injury_penalty = compute_injury_detractor(nba_data, threshold=60, seasons_to_consider=5, penalty_per_season=2.0)
    age_penalty = compute_age_penalty(age, threshold=36, penalty_per_year=2.0)

    # Combine components into final AVN using hyperparameters:
    w_perf = 0.30
    w_awards = 0.30
    w_rating = 0.4

    AVN = (w_perf * base_perf * ym) + (w_awards * awards_bonus) + (w_rating * rating_mult * base_perf)
    AVN -= injury_penalty
    AVN -= age_penalty

    stats = {
        "Player Age": age,
        "Age Weights (prev, curr)": f"({weight_prev}, {weight_current})",
        "Young Multiplier": ym,
        "Current Season Score": current_score,
        "Previous Season Score": previous_score,
        "Base Performance Score": base_perf,
        "Awards Bonus": awards_bonus,
        "Historical Rating": current_rating,
        "Rating Multiplier": rating_mult,
        "Injury Detractor": injury_penalty,
        "Age Penalty": age_penalty,
        "Final AVN": AVN
    }
    
    print_stats_table(stats)
    
    return AVN

# ---------- Database Update ----------

def update_avn_for_all_players(db_path="players.db"):
    """
    For each player in the database, compute their AVN and update the 'avn' column.
    If the 'avn' column does not exist, it is added.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(players)")
    columns = [col[1] for col in c.fetchall()]
    if "avn" not in columns:
        print("Column 'avn' not found. Adding it to the players table...")
        c.execute("ALTER TABLE players ADD COLUMN avn REAL")
        conn.commit()
    
    df = pd.read_sql_query("SELECT name, current_age, nba_data, nba_awards, all_star_selections, historical_ratings, height FROM players", conn)
    
    for index, row in df.iterrows():
        player_record = row.to_dict()
        print(f"\n--- Processing {player_record.get('name')} ---")
        avn_value = compute_AVN(player_record)
        c.execute("UPDATE players SET avn = ? WHERE name = ?", (avn_value, player_record.get("name")))
        conn.commit()
        print(f"Updated AVN for {player_record.get('name')}: {avn_value:.2f}")
    
    conn.close()
    print("\nAll player records have been updated with AVN.")

# ---------- Example Usage ----------

if __name__ == "__main__":
    # Example: compute and print AVN for a single player
    player_name = "Victor Wembanyama"  # Change as needed
    record = load_player(player_name)
    if record:
        avn_value = compute_AVN(record)
        print(f"\nAsset Value Number for {player_name}: {avn_value:.2f}")
    else:
        print(f"No record found for {player_name}.")

    # Update AVN for all players in the database
    update_avn_for_all_players()
