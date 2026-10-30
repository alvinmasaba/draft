#!/usr/bin/env python3
"""
create_features_csv.py

This script connects to the players SQLite database, loads each player's record,
parses the NBA stats (in JSON format), computes various features (e.g., average performance
over the last three seasons, injury detractor, awards bonus, current rating factor, young-age multiplier, etc.),
and writes the resulting feature set to a CSV file.
"""

import sqlite3
import pandas as pd
import json
import re
from datetime import datetime

# ---------------- Helper Functions ----------------

def season_to_year(season_str):
    """
    Convert a season string like "2023-24" into its start year as an integer.
    Returns None if conversion fails or if season_str is 'CAREER'.
    """
    if not season_str or "CAREER" in season_str.upper():
        return None
    try:
        return int(season_str.split("-")[0])
    except Exception:
        return None

def get_last_n_seasons(nba_data, n=3):
    """
    Given nba_data (a list of season dicts), return the last n seasons (sorted descending by start year).
    """
    valid_seasons = [s for s in nba_data if season_to_year(s.get("season", "")) is not None]
    valid_seasons.sort(key=lambda s: season_to_year(s.get("season", "")), reverse=True)
    return valid_seasons[:n]

def compute_season_performance(season_stats):
    """
    Compute a performance score for one season based on key features.
    A discount factor is applied if the season's games played ('gp') is low.
    """
    feature_weights = {
        'ws': 0.85,       
        'per': 0.6,       
        'ortg': 1.2,      
        'ppg': 1.7,       
        'fgm': 1.0,       
        'trb': 0.55,      
        'ts%': 0.7,       
        'stl': 0.4,       
        'drtg': -0.5,     
        'ftm': 0.4,       
        'blk': 0.75,      
        'usg%': 0.8,      
        'ows': 1.1,       
        'dws': 0.6,       
        '3p_pct': 0.75,   
        'ast%': 0.55,     
        'min': 0.4,       
    }
    try:
        gp = float(season_stats.get("gp", 0))
    except Exception:
        gp = 0.0
    threshold = 25.0  # adjust as needed
    discount_factor = min(1.0, gp / threshold)
    score = 0.0
    for feature, weight in feature_weights.items():
        try:
            value = float(season_stats.get(feature, 0))
        except Exception:
            value = 0.0
        score += weight * value
    score *= discount_factor
    return score

def get_age_weights(age):
    """
    Return (previous_weight, current_weight) based on player's age.
    
    Age Ranges:
      - 19-22: (0.25, 0.75)
      - 23-26: (0.40, 0.60)
      - 27-30: (0.50, 0.50)
      - 31-34: (0.45, 0.55)
      - 35-37: (0.325, 0.675)
      - 38+:   (0.10, 0.90)
    """
    if age < 19:
        return (0.25, 0.75)
    elif age <= 22:
        return (0.25, 0.75)
    elif age <= 26:
        return (0.40, 0.60)
    elif age <= 30:
        return (0.50, 0.50)
    elif age <= 34:
        return (0.45, 0.55)
    elif age <= 37:
        return (0.325, 0.675)
    else:
        return (0.10, 0.90)

def young_multiplier(age, current_rating):
    """
    For players under 26, compute a bonus multiplier based on age and current rating.
    For example, a younger player with a high rating receives a bigger bonus.
    """
    if age < 26:
        rating_bonus = max(0, current_rating - 70)
        bonus = ((25 - age) / 7) * (rating_bonus / 30) * 0.95
        return 1 + bonus
    else:
        return 1.0

def compute_injury_detractor(nba_data, threshold=60, seasons_to_consider=5, penalty_per_season=2.0):
    """
    Look at the last `seasons_to_consider` seasons. Count how many have 'gp' below threshold.
    If more than one season is low, apply a penalty per extra season.
    """
    valid_seasons = [s for s in nba_data if season_to_year(s.get("season", "")) is not None]
    valid_seasons.sort(key=lambda s: season_to_year(s.get("season", "")), reverse=True)
    recent_seasons = valid_seasons[:seasons_to_consider]
    low_gp_count = 0
    for season in recent_seasons:
        try:
            gp = float(season.get("gp", 0))
        except Exception:
            gp = 0.0
        if gp < threshold:
            low_gp_count += 1
    if low_gp_count > 1:
        return (low_gp_count - 1) * penalty_per_season
    return 0.0

def compute_detailed_awards_bonus(awards_json, all_star_json, current_year):
    """
    Compute an awards bonus from the awards and all-star JSON.
    (For training purposes you can include every award as a feature; here we simply return a total bonus.)
    Only awards from the past 5 years (relative to current_year) are considered.
    """
    # For brevity, here we return 0.0. (You can expand this function to parse and sum only specific awards.)
    return 0.0, {}

def rating_factor(current_rating):
    """
    Convert current rating into a factor (e.g., if typical ratings are in the 70–90 range, divide by 80).
    """
    try:
        rating = float(current_rating)
        return rating / 80.0
    except Exception:
        return 1.0

def get_current_rating_from_history(hist_ratings_json):
    """
    Extract the current rating from the historical ratings JSON.
    Uses the season with the highest start year.
    """
    try:
        hist_ratings = json.loads(hist_ratings_json) if hist_ratings_json else {}
        if not hist_ratings:
            return 80.0
        season_ratings = []
        for season_str, rating in hist_ratings.items():
            try:
                start_year = int(season_str.split("-")[0])
                season_ratings.append((start_year, float(rating)))
            except Exception:
                continue
        if not season_ratings:
            return 80.0
        latest_rating = max(season_ratings, key=lambda x: x[0])[1]
        return latest_rating
    except Exception:
        return 80.0

# ---------------- Create Features CSV ----------------

def create_features_csv(db_path="players.db", output_csv="player_features.csv"):
    """
    Connects to the SQLite database, computes a feature vector for each player,
    and writes all features to a CSV file.
    """
    # Load the entire players table
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM players", conn)
    conn.close()
    
    features_list = []
    for idx, row in df.iterrows():
        record = row.to_dict()
        # Parse the player's NBA data JSON field
        try:
            nba_data = json.loads(record.get("nba_data", "[]"))
        except Exception:
            nba_data = []
        # Get last three seasons (if available)
        last_three = get_last_n_seasons(nba_data, n=3)
        if last_three:
            perf_scores = [compute_season_performance(season) for season in last_three]
            avg_perf = sum(perf_scores) / len(perf_scores)
        else:
            avg_perf = 0.0

        # Injury detractor based on the last 5 seasons
        injury_penalty = compute_injury_detractor(nba_data, threshold=60, seasons_to_consider=5, penalty_per_season=2.0)
        
        # Awards bonus (using our simplified function)
        current_year = datetime.now().year
        awards_bonus, _ = compute_detailed_awards_bonus(record.get("nba_awards", "{}"),
                                                        record.get("all_star_selections", "{}"),
                                                        current_year)
        # Current historical 2K rating and rating multiplier
        current_rating = get_current_rating_from_history(record.get("historical_ratings", "{}"))
        r_mult = rating_factor(current_rating)
        
        # Age and young multiplier
        try:
            age = float(record.get("current_age", 25))
        except Exception:
            age = 25.0
        age_weights = get_age_weights(age)  # returns (prev, curr)
        ym = young_multiplier(age, current_rating)
        
        # For the base performance, if we have at least two seasons, use a weighted average of the top two.
        if len(last_three) >= 2:
            current_score = compute_season_performance(last_three[0])
            previous_score = compute_season_performance(last_three[1])
            weight_prev, weight_current = age_weights
            base_perf = (weight_prev * previous_score) + (weight_current * current_score)
        elif last_three:
            base_perf = compute_season_performance(last_three[0])
        else:
            base_perf = 0.0
        
        # Compute a final AVN (using hyperparameters similar to your AVN module)
        final_AVN = (0.43 * base_perf * ym) + (0.16 * awards_bonus) + (0.41 * r_mult * base_perf) - injury_penalty

        # Build a feature dictionary for this player
        features = {
            "name": record.get("name"),
            "age": age,
            "position": record.get("position"),
            "height": record.get("height"),
            "weight": record.get("weight"),
            "wingspan": record.get("wingspan"),
            "archetype": record.get("archetype"),
            "avg_perf_last_3": avg_perf,
            "injury_penalty": injury_penalty,
            "awards_bonus": awards_bonus,
            "current_rating": current_rating,
            "rating_multiplier": r_mult,
            "young_multiplier": ym,
            "base_perf": base_perf,
            "final_AVN": final_AVN
        }
        
        # Optionally, include raw stats from the most recent season
        if last_three:
            most_recent = last_three[0]
            for key, value in most_recent.items():
                features[f"recent_{key}"] = value
        
        features_list.append(features)
    
    features_df = pd.DataFrame(features_list)
    features_df.to_csv(output_csv, index=False)
    print(f"Features CSV created at: {output_csv}")

if __name__ == "__main__":
    create_features_csv()
