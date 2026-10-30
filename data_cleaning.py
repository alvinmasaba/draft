import pandas as pd
import ast
import re
import json
from helpers.cleaning_helpers import (
    add_additional_keys,
    convert_dicts,
    process_awards_dicts
)

def clean_and_convert_nba_data(value):
    """
    Cleans a string representation of a list (e.g., NBA season stats)
    and converts it into a Python object using ast.literal_eval.
    
    It also removes asterisks and replaces 'nan' with 'None'.
    """
    if not isinstance(value, str):
        return value
    cleaned_value = value.replace('nan', 'None')
    cleaned_value = re.sub(r'\*', '', cleaned_value)
    try:
        return ast.literal_eval(cleaned_value)
    except (SyntaxError, ValueError):
        print("Error parsing nba_data:", value)
        return []

def clean_data(df):
    """
    Cleans the player DataFrame by:
      - Adding additional keys (e.g., converting height to inches)
      - Converting awards fields from string representations to dictionaries
      - Cleaning the nba_data column using clean_and_convert_nba_data
      - Processing awards dictionaries into a standardized format.
    """
    pd.set_option('display.max_columns', None)
    df = add_additional_keys(df)
    df = convert_dicts(df, ['nba_awards', 'all_star_selections'])
    
    # Clean the nba_data column: convert from string to a Python object.
    df['nba_data'] = df['nba_data'].apply(
        lambda x: clean_and_convert_nba_data(x) if isinstance(x, str) else x
    )
    # Optionally, convert any remaining valid JSON strings.
    df['nba_data'] = df['nba_data'].apply(
        lambda x: json.loads(x) if isinstance(x, str) else x
    )
    
    df = process_awards_dicts(df, ['nba_awards', 'all_star_selections'])
    return df

def expand_nba_data(row):
    """
    Expands the nba_data list (each element corresponds to one season's stats)
    into separate columns where the keys are appended with the season string.
    """
    expanded_data = {}
    nba_seasons = row.get('nba_data', [])
    for item in nba_seasons:
        season = item.get('season', '').replace(' *', '')
        for key, value in item.items():
            if key != 'season':
                expanded_data[f"{key}_{season}"] = value
    return expanded_data

if __name__ == "__main__":
    # For example, load data from the SQLite database and then export cleaned CSV.
    import sqlite3
    conn = sqlite3.connect("players.db")
    df = pd.read_sql_query("SELECT * FROM players", conn)
    conn.close()
    
    df = clean_data(df)
    df.to_csv("./data/database/clean/cleaned_player_data.csv", index=False)
    
    # Optionally, expand the nba_data into separate columns:
    # expanded_columns = df.apply(expand_nba_data, axis=1)
    # expanded_df = pd.concat([df, expanded_columns], axis=1).drop(columns=['nba_data'])
    # print(expanded_df.head())
