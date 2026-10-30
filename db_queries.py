#!/usr/bin/env python3
import sqlite3
import pandas as pd
from tabulate import tabulate

def get_top_players(db_path="players.db", top_n=50):
    """
    Retrieve the top N players by AVN from the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    query = """
        SELECT name, avn 
        FROM players 
        WHERE avn IS NOT NULL 
        ORDER BY avn DESC 
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(top_n,))
    conn.close()
    return df

def main():
    df = get_top_players()
    if df.empty:
        print("No players with AVN found in the database.")
    else:
        print("\nTop 50 Players by AVN:")
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

if __name__ == "__main__":
    main()
