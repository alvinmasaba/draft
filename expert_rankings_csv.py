import pandas as pd

# Expert ranking list (from best to worst)
EXPERT_RANKS = [
    'Victor Wembanyama', 'Shai Gilgeous-Alexander', 'Nikola Jokic', 'Giannis Antetokounmpo', 'Luka Doncic', 'Stephen Curry', 'Anthony Edwards',
    'Anthony Davis', 'Jayson Tatum', 'Cade Cunningham', 'Ja Morant', 'Franz Wagner', 'Evan Mobley', 'Donovan Mitchell', 'Devin Booker', 'Paolo Banchero', 'Joel Embiid', 
    'LaMelo Ball', 'Tyrese Maxey', 'Chet Holgrem', 'Alperen Sengun', 'Karl-Anthony Towns', 'Jaylen Brown', 'Jalen Williams', 'Kyrie Irving', 'Jalen Brunson',
    'Amen Thompson', 'Scottie Barnes', 'Kevin Durant', 'Zion Williamson', 'De\'Aaron Fox', 'LeBron James', 'Tyrese Haliburton', 'Jaren Jackson Jr.', 'Darius Garland', 
    'Domantas Sabonis', 'James Harden', 'Damian Lillard', 'Trae Young', 'Jimmy Butler', 'Lauri Markkanen', 'Pascal Siakam', 'Derrick White', 'Jalen Johnson', 
    'Trey Murphy III', 'Tyler Herro', 'Jarrett Allen', 'Desmond Bane', 'Bam Adebayo', 'Rudy Gobert'#, 'Jamal Murray', 'Jalen Green', 'Michael Porter Jr.', 
    # 'Kristaps Porzingis', 'Austin Reaves', 'Brandon Ingram', 'Norman Powell', 'Julius Randle', 'Dyson Daniels'
]

def assign_expert_ranks(input_csv, output_csv):
    # Load CSV data that has a column 'player_name'
    df = pd.read_csv(input_csv)
    
    # Create a mapping from player name to expert rank.
    # Here, rank 1 means best, 2 means second-best, etc.
    rank_mapping = {name: rank for rank, name in enumerate(EXPERT_RANKS, start=1)}
    
    # Assign expert_value only if the player is in expert list; otherwise, can choose to drop or assign NaN.
    df['expert_value'] = df['player_name'].apply(lambda name: rank_mapping.get(name, None))
    
    # Optionally, drop rows without an expert_value (if training only on these 75 players)
    df = df.dropna(subset=['expert_value'])
    
    # Save the new CSV file
    df.to_csv(output_csv, index=False)
    print(f"Saved updated CSV with expert ranks to {output_csv}")

if __name__ == "__main__":
    input_csv = "all_players.csv"    # original CSV file with player data including a 'player_name' column
    output_csv = "top75_expert_ranks.csv"
    assign_expert_ranks(input_csv, output_csv)
