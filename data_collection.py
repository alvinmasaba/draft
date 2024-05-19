from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
from models.player import Player

def find_target_table(soup):
    tables = soup.find_all('table')
    for table in tables:
        if table.find("thead") and table.find("tbody"):
            return table
    return None

def create_player(row):
    name = row.find("a").text
    player_url = "https://basketball.realgm.com" + row.find("a")["href"]
    position = row.find("td", {"data-th": "Pos"}).text
    height = row.find("td", {"data-th": "Height"}).text
    weight = row.find("td", {"data-th": "Weight"}).text
    school = row.find("td", {"data-th": "Pre-Draft Team"}).text
    pick = row.find("td", {"data-th": "Draft Status"}).text
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

def save_players_to_csv(players):
    if players:
        # Convert the player data to a Pandas DataFrame
        player_data = [player.to_dict() for player in players]
        new_df = pd.DataFrame(player_data)

        # If players.csv exists, load it and append new data
        if os.path.exists("players.csv"):
            existing_df = pd.read_csv("players.csv")
            existing_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            existing_df = new_df

        # Sort the DataFrame alphabetically by player's name
        if not existing_df.empty:
            existing_df.sort_values('name', inplace=True)

        # Save the DataFrame to a CSV file
        existing_df.to_csv("players.csv", index=False)

        # Clear players list
        players = []

def collect_data():
    players = []
    player_names = set()

    if os.path.exists("players.csv"):
        df = pd.read_csv("players.csv")
        player_names = set(df['name'])

    for year in range(2011, 2017):
        print(f"{year}")
        url = f"https://basketball.realgm.com/nba/players/{year}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = find_target_table(soup)
        rows = table.find_all("tr")

        for i, row in enumerate(rows[1:], 1):
            name = row.find("a").text
            print(f"{name}")
            
            if name not in player_names:
                player = create_player(row)

                player.scrape_ncaa_data()
                player.scrape_nba_data()
                players.append(player)
                player_names.add(name)

                # Save checkpoint every 50 players
                if i % 50 == 0:
                    print('Checkpoint...')
                    save_players_to_csv(players)
                    players.clear()  # Clear players list here


if __name__ == "__main__":
    collect_data()

def create_player(row):
    name = row.find("a").text
    player_url = "https://basketball.realgm.com" + row.find("a")["href"]
    position = row.find("td", {"data-th": "Pos"}).text
    height = row.find("td", {"data-th": "Height"}).text
    weight = row.find("td", {"data-th": "Weight"}).text
    school = row.find("td", {"data-th": "Pre-Draft Team"}).text
    pick = row.find("td", {"data-th": "Draft Status"}).text
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

def save_players_to_csv(players):
    if players:
        # Convert the player data to a Pandas DataFrame
        player_data = [player.to_dict() for player in players]
        new_df = pd.DataFrame(player_data)

        # If players.csv exists, load it and append new data
        if os.path.exists("players.csv"):
            existing_df = pd.read_csv("players.csv")
            existing_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            existing_df = new_df

        # Sort the DataFrame alphabetically by player's name
        if not existing_df.empty:
            existing_df.sort_values('name', inplace=True)

        # Save the DataFrame to a CSV file
        existing_df.to_csv("players.csv", index=False)

        # Clear players list
        players = []

def collect_data():
    players = []
    player_names = set()

    if os.path.exists("players.csv"):
        df = pd.read_csv("players.csv")
        player_names = set(df['name'])

    for year in range(2011, 2017):
        print(f"{year}")
        url = f"https://basketball.realgm.com/nba/players/{year}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = find_target_table(soup)
        rows = table.find_all("tr")

        for i, row in enumerate(rows[1:], 1):
            name = row.find("a").text
            print(f"{name}")
            
            if name not in player_names:
                player = create_player(row)

                player.scrape_ncaa_data()
                player.scrape_nba_data()
                players.append(player)
                player_names.add(name)

                # Save checkpoint every 50 players
                if i % 50 == 0:
                    print('Checkpoint...')
                    save_players_to_csv(players)
                    players.clear()  # Clear players list here

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

class PlayerScraper:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_soup(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        else:
            print(f"Failed to retrieve content from {url}")
            return None

    def parse_player_data(self, soup):
        player_data = []
        for row in soup.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            player_data.append({
                'name': cols[0].text.strip(),
                'position': cols[1].text.strip(),
                'height': cols[2].text.strip(),
                'weight': cols[3].text.strip(),
                'school': cols[4].text.strip(),
                'conference': cols[5].text.strip(),
                'draft_year': cols[6].text.strip()
            })
        return player_data

    def scrape_players(self, start_page, end_page):
        all_player_data = []
        for page in range(start_page, end_page + 1):
            url = f"{self.base_url}?page={page}"
            print(f"Scraping {url}...")
            soup = self.get_soup(url)
            if soup:
                player_data = self.parse_player_data(soup)
                all_player_data.extend(player_data)
            time.sleep(1)  # To avoid overwhelming the server
        return all_player_data

if __name__ == "__main__":
    base_url = "https://basketball.realgm.com/player"
    scraper = PlayerScraper(base_url)
    player_data = scraper.scrape_players(1, 10)  # Adjust page range as needed
    df = pd.DataFrame(player_data)
    df.to_csv('./data/database/raw/player_data.csv', index=False)
