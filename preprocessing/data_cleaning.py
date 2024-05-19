import pandas as pd
from helpers.cleaning_helpers import *

def clean_data(df):
    df = clean_draft_pick(df)
    df = add_additional_keys(df)
    df = convert_dicts(df, ['ncaa_data', 'ncaa_awards', 'nba_data', 'nba_awards', 'all_star_selections'])
    df = process_awards_dicts(df, ['nba_awards', 'ncaa_awards', 'all_star_selections'])
    df = transform_null_values(df)
    df = extract_data(df)
    df = calc_per40_stats(df, NUMERIC_STATS)
    df = df.join(df.apply(extract_nba_career_data, axis=1))
    df = normalize_values(df, NUMERIC_STATS)
    return df

if __name__ == "__main__":
    df = pd.read_csv("./data/database/raw/player_data.csv")
    df = check_for_ncaa_data(df)
    df = clean_data(df)
    df.to_csv("./data/database/clean/cleaned_player_data.csv", index=False)
