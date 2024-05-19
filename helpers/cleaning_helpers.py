import pandas as pd
import numpy as np
import os

NUMERIC_STATS = ['gp', 'gs', 'min', 'ppg', 'fgm', 'fga', '3pm', '3pa', 'ftm', 'fta', 'orb', 'drb', 'trb', 'ast', 'stl', 'blk', 'tov', 'pf']
ADVANCED_STATS = ['fg%', '3p%', 'ft%', 'ast/to', 'ows', 'dws', 'ws', 'ts%', 'efg%', 'orb%', 'drb%', 'trb%', 'ast%', 'tov%', 'stl%', 'blk%', 'usg%', 'pps', 'ortg', 'drtg', 'per']

def convert_height_to_inches(height):
    feet, inches = height.split('-')
    return int(feet) * 12 + int(inches)

def convert_str_to_dict(s):
    try:
        return eval(s)
    except:
        return {}

def clean_awards(awards_dict):
    cleaned_awards = {}
    for award, years in awards_dict.items():
        cleaned_awards[award] = [int(year) for year in years if year.isdigit()]
    return cleaned_awards

def normalize_values(df, columns):
    for column in columns:
        mean = df[column].mean()
        std = df[column].std()
        df[column] = (df[column] - mean) / std
    return df

def save_mean_and_std(stat, mean, std):
    with open(os.path.join('data', 'transformations', f"{stat}_norm_params.txt"), 'w') as f:
        f.write(f"{mean},{std}")

def check_for_ncaa_data(df):
    df['ncaa_data_complete'] = df['ncaa_data'].apply(lambda x: bool(x))
    return df

def calc_per40_stats(df, numeric_stats):
    for stat in numeric_stats[3:]:
        df[f'ncaa_{stat}_per_40'] = df[f'ncaa_{stat}_final_season'] * (40 / df['ncaa_min_final_season'])
    return df

def extract_final_season_stats(df, i, season_data):
    for stat, value in season_data.items():
        if stat in NUMERIC_STATS or stat in ADVANCED_STATS:
            df.at[i, stat] = value
            df[stat] = pd.to_numeric(df[stat], errors='coerce')
            if stat in NUMERIC_STATS:
                df = calc_totals(df, season_data, stat, value, i)
    return df

def calc_totals(df, data, stat, value, i):
    if stat not in ['gp', 'gs'] and 'gp' in data:
        value = pd.to_numeric(value, errors='coerce')
        data['gp'] = pd.to_numeric(data['gp'], errors='coerce')
        if pd.notna(value) and pd.notna(data['gp']):
            df.at[i, f'{stat}_total'] = round(value * data['gp'])
    return df

def extract_nba_career_data(data):
    total_per, total_ppg, total_ws, total_ortg, total_games = 0, 0, 0, 0, 0
    for season_data in data['nba_data']:
        total_per += float(season_data['per']) if season_data['per'] != '-' else 0
        total_ws += float(season_data['ws']) if season_data['ws'] != '-' else 0
        total_ortg += float(season_data['ortg']) if season_data['ortg'] != '-' else 0
        total_games += season_data['gp']
    num_seasons = len(data['nba_data'])
    career_avg_per = (total_per / num_seasons) if num_seasons != 0 else 0
    career_avg_ppg = (total_ppg / num_seasons) if num_seasons != 0 else 0
    career_avg_ws = (total_ws / num_seasons) if num_seasons != 0 else 0
    career_avg_ortg = (total_ortg / num_seasons) if num_seasons != 0 else 0
    total_points = career_avg_ppg * total_games
    return pd.Series({'Career Average PER': career_avg_per, 'Career Average PPG': career_avg_ppg, 'Career Average WS': career_avg_ws, 'Career Average ORTG': career_avg_ortg, 'Total Points': total_points})

def add_additional_keys(df):
    df['height'] = df['height'].apply(convert_height_to_inches)
    df = normalize_values(df, ['draft_age', 'height', 'weight'])
    return df

def clean_draft_pick(df):
    df['draft_pick'] = df['draft_pick'].replace('Undrafted', 61).astype(int)
    return df

def convert_dicts(df, dicts):
    for dict_name in dicts:
        df[dict_name] = df[dict_name].apply(convert_str_to_dict)
    return df

def process_awards_dicts(df, awards_dicts):
    for awards_dict in awards_dicts:
        df[awards_dict] = df[awards_dict].apply(clean_awards)
    return df

def transform_null_values(df):
    for dict_name in ['ncaa_data', 'ncaa_awards', 'nba_data', 'nba_awards']:
        df[dict_name].fillna("{}", inplace=True)
    return df

def extract_data(df):
    for i, row in df.iterrows():
        if row['ncaa_data']:
            final_season = row['ncaa_data'][-1]
            df = extract_final_season_stats(df, i, final_season)
    return df
