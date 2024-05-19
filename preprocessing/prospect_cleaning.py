import pandas as pd
from cleaning_helpers import *

def clean_data(df):
    df = add_additional_keys(df)
    df = convert_dicts(df, ['ncaa_data'])
    df = transform_null_values(df)
    df = extract_data(df)
    # df = calc_per40_stats(df, NUMERIC_STATS)
    df = normalize_values(df, NUMERIC_STATS)
    return df

if __name__ == "__main__":
    df = pd.read_csv("../data/database/raw/prospects.csv")
    df = check_for_ncaa_data(df)
    df = clean_data(df)
    df.to_csv("../data/database/clean/cleaned_prospect_data.csv", index=False)
