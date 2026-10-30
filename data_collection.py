import os
import sqlite3
import time
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
from models.player import Player

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/58.0.3029.110 Safari/537.3'
}

def find_target_table(soup):
    tables = soup.find_all('table')
    for table in tables:
        if table.find("thead") and table.find("tbody"):
            return table
    return None

def create_player(row):
    name = row.find("a").text.strip()
    player_url = "https://basketball.realgm.com" + row.find("a")["href"]
    position = row.find("td", {"data-th": "Pos"}).text.strip()
    height = row.find("td", {"data-th": "Height"}).text.strip()
    weight = row.find("td", {"data-th": "Weight"}).text.strip()
    school = row.find("td", {"data-th": "Pre-Draft Team"}).text.strip()
    pick = row.find("td", {"data-th": "Draft Status"}).text.strip()
    player = Player(
        name=name, 
        url=player_url,
        position=position, 
        height=height, 
        weight=weight, 
        school=school, 
        pick=pick
    )
    return player

def save_players_to_db(players):
    # Connect to (or create) the SQLite database.
    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    
    # Create the players table if it does not already exist.
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            name TEXT PRIMARY KEY,
            url TEXT,
            position TEXT,
            height TEXT,
            weight TEXT,
            school TEXT,
            pick TEXT,
            current_age INTEGER,
            nba_data TEXT,
            nba_awards TEXT,
            all_star_selections TEXT,
            rating_2k TEXT,
            historical_ratings TEXT,
            wingspan INTEGER,
            archetype TEXT
        )
    ''')
    
    for player in players:
        data = player.to_dict()
        c.execute('''
            INSERT OR REPLACE INTO players 
            (name, url, position, height, weight, school, pick, current_age, nba_data, nba_awards, all_star_selections, rating_2k, historical_ratings, wingspan, archetype)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name'),
            data.get('url'),
            data.get('position'),
            data.get('height'),
            data.get('weight'),
            data.get('school'),
            data.get('pick'),
            data.get('age'),
            json.dumps(data.get('nba_data')),
            data.get('nba_awards'),
            data.get('all_star_selections'),
            data.get('rating_2k'),
            data.get('historical_ratings'),
            data.get('wingspan'),
            data.get('archetype')
        ))
    conn.commit()
    conn.close()

def collect_data():
    players = []
    existing_names = set()
    # Load existing player names from the database (if it exists)
    if os.path.exists("players.db"):
        conn = sqlite3.connect("players.db")
        c = conn.cursor()
        c.execute("SELECT name FROM players")
        rows = c.fetchall()
        existing_names = set(row[0] for row in rows)
        conn.close()
    
    for year in range(2021, 2025):
        print(f"Processing year: {year}")
        url = f"https://basketball.realgm.com/nba/players/{year}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = find_target_table(soup)
        if table is None:
            print("No target table found for this page.")
            continue
        rows = table.find_all("tr")
        for i, row in enumerate(rows[1:], 1):
            name = row.find("a").text.strip()
            print(f"Processing player: {name}")
            if name not in existing_names:
                player = create_player(row)
                # Scrape NBA data from RealGM (includes wingspan and archetype)
                player.scrape_nba_data()
                # Scrape the current and historical 2K ratings using our headless browser workaround
                player.scrape_2kratings_data()
                players.append(player)
                existing_names.add(name)
                
                # Save checkpoint every 50 players
                if i % 50 == 0:
                    print("Saving checkpoint to DB...")
                    save_players_to_db(players)
                    players.clear()
                    time.sleep(2)
    # Save any remaining players.
    if players:
        save_players_to_db(players)

if __name__ == "__main__":
    collect_data()



# from bs4 import BeautifulSoup
# import requests
# import pandas as pd
# import os
# from models.player import Player

# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# def find_target_table(soup):
#     tables = soup.find_all('table')
#     for table in tables:
#         if table.find("thead") and table.find("tbody"):
#             return table
#     return None

# def create_player(row):
#     name = row.find("a").text
#     player_url = "https://basketball.realgm.com" + row.find("a")["href"]
#     position = row.find("td", {"data-th": "Pos"}).text
#     height = row.find("td", {"data-th": "Height"}).text
#     weight = row.find("td", {"data-th": "Weight"}).text
#     school = row.find("td", {"data-th": "Pre-Draft Team"}).text
#     pick = row.find("td", {"data-th": "Draft Status"}).text
#     player = Player(
#         name=name, 
#         url=player_url,
#         position=position, 
#         height=height, 
#         weight=weight, 
#         school=school, 
#         pick=pick
#     )
#     return player

# def save_players_to_csv(players):
#     if players:
#         # Convert the player data to a Pandas DataFrame
#         player_data = [player.to_dict() for player in players]
#         new_df = pd.DataFrame(player_data)

#         # If players.csv exists, load it and append new data
#         if os.path.exists("players.csv"):
#             existing_df = pd.read_csv("players.csv")
#             existing_df = pd.concat([existing_df, new_df], ignore_index=True)
#         else:
#             existing_df = new_df

#         # Sort the DataFrame alphabetically by player's name
#         if not existing_df.empty:
#             existing_df.sort_values('name', inplace=True)

#         # Save the DataFrame to a CSV file
#         existing_df.to_csv("players.csv", index=False)

#         # Clear players list
#         players = []

# def collect_data():
#     players = []
#     player_names = set()

#     if os.path.exists("players.csv"):
#         df = pd.read_csv("players.csv")
#         player_names = set(df['name'])

#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
#     for year in range(2021, 2025):
#         print(f"{year}")
#         url = f"https://basketball.realgm.com/nba/players/{year}"
#         response = requests.get(url, headers=headers)
#         soup = BeautifulSoup(response.text, 'html.parser')
#         table = find_target_table(soup)
#         rows = table.find_all("tr")

#         for i, row in enumerate(rows[1:], 1):
#             name = row.find("a").text
#             print(f"{name}")
            
#             if name not in player_names:
#                 player = create_player(row)

#                 # player.scrape_ncaa_data()
#                 player.scrape_nba_data()
#                 players.append(player)
#                 player_names.add(name)

#                 # Save checkpoint every 50 players
#                 if i % 50 == 0:
#                     print('Checkpoint...')
#                     save_players_to_csv(players)
#                     players.clear()  # Clear players list here


# if __name__ == "__main__":
#     collect_data()

# def create_player(row):
#     name = row.find("a").text
#     player_url = "https://basketball.realgm.com" + row.find("a")["href"]
#     position = row.find("td", {"data-th": "Pos"}).text
#     height = row.find("td", {"data-th": "Height"}).text
#     weight = row.find("td", {"data-th": "Weight"}).text
#     school = row.find("td", {"data-th": "Pre-Draft Team"}).text
#     pick = row.find("td", {"data-th": "Draft Status"}).text
#     player = Player(
#         name=name, 
#         url=player_url,
#         position=position, 
#         height=height, 
#         weight=weight, 
#         school=school, 
#         pick=pick,
#     )
#     return player

# def save_players_to_csv(players):
#     if players:
#         # Convert the player data to a Pandas DataFrame
#         player_data = [player.to_dict() for player in players]
#         new_df = pd.DataFrame(player_data)

#         # If players.csv exists, load it and append new data
#         if os.path.exists("players.csv"):
#             existing_df = pd.read_csv("players.csv")
#             existing_df = pd.concat([existing_df, new_df], ignore_index=True)
#         else:
#             existing_df = new_df

#         # Sort the DataFrame alphabetically by player's name
#         if not existing_df.empty:
#             existing_df.sort_values('name', inplace=True)

#         # Save the DataFrame to a CSV file
#         existing_df.to_csv("players.csv", index=False)

#         # Clear players list
#         players = []

# def collect_data():
#     players = []
#     player_names = set()

#     if os.path.exists("players.csv"):
#         df = pd.read_csv("players.csv")
#         player_names = set(df['name'])

#     for year in range(2021, 2025):
#         print(f"{year}")
#         url = f"https://basketball.realgm.com/nba/players/{year}"
#         response = requests.get(url, headers=headers)
#         soup = BeautifulSoup(response.text, 'html.parser')
#         table = find_target_table(soup)
#         rows = table.find_all("tr")

#         for i, row in enumerate(rows[1:], 1):
#             name = row.find("a").text
#             print(f"{name}")
            
#             if name not in player_names:
#                 player = create_player(row)

#                 # player.scrape_ncaa_data()
#                 player.scrape_nba_data()
#                 players.append(player)
#                 player_names.add(name)

#                 # Save checkpoint every 50 players
#                 if i % 50 == 0:
#                     print('Checkpoint...')
#                     save_players_to_csv(players)
#                     players.clear()  # Clear players list here

# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import time

# class PlayerScraper:
#     def __init__(self, base_url):
#         self.base_url = base_url

#     def get_soup(self, url):
#         response = requests.get(url)
#         if response.status_code == 200:
#             return BeautifulSoup(response.content, 'html.parser')
#         else:
#             print(f"Failed to retrieve content from {url}")
#             return None

#     def parse_player_data(self, soup):
#         player_data = []
#         rows = soup.find_all('tr')
#         for row in rows[1:]:
#             cols = row.find_all('td')
#             # Expected number of columns for a valid player row, e.g., 7 columns
#             if len(cols) < 7:
#                 print("Warning: row does not have expected number of columns (found", len(cols), "). Skipping row.")
#                 continue
#             player_data.append({
#                 'name': cols[0].text.strip(),
#                 'position': cols[1].text.strip(),
#                 'height': cols[2].text.strip(),
#                 'weight': cols[3].text.strip(),
#                 'school': cols[4].text.strip(),
#                 'conference': cols[5].text.strip(),
#                 'draft_year': cols[6].text.strip()
#             })
#         return player_data


#     def scrape_players(self, start_page, end_page):
#         all_player_data = []
#         for page in range(start_page, end_page + 1):
#             url = f"{self.base_url}?page={page}"
#             print(f"Scraping {url}...")
#             soup = self.get_soup(url)
#             if soup:
#                 player_data = self.parse_player_data(soup)
#                 all_player_data.extend(player_data)
#             time.sleep(1)  # To avoid overwhelming the server
#         return all_player_data

# if __name__ == "__main__":
#     base_url = "https://basketball.realgm.com/player"
#     scraper = PlayerScraper(base_url)
#     player_data = scraper.scrape_players(1, 10)  # Adjust page range as needed
#     df = pd.DataFrame(player_data)
#     df.to_csv('data/database/raw/player_data_2022-2024.csv', index=False)
