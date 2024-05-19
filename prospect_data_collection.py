from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
from models.player import Player
from data.prospects_list_2023 import ncaa_prospects, ignite_prospects, int_prospects

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def find_target_table(soup):
    tables = soup.find_all('table')
    for table in tables:
        if table.find("thead") and table.find("tbody"):
            return table
    return None

def create_player(row):
    name = row.find("a").text
    player_url = "https://basketball.realgm.com" + row.find("a")["href"]
    tds = row.find_all("td")
    position = tds[1].text  # Assuming position is in the second td element
    height = tds[2].text  # Assuming height is in the third td element
    weight = tds[3].text  # Assuming weight is in the fourth td element
    school = tds[4].text  # Assuming school is in the fifth td element
    dob = tds[6].text  # Assuming DOB is in the sixth td element

    player = Player(
        name=name, 
        url=player_url,
        position=position, 
        height=height, 
        weight=weight, 
        school=school, 
        dob=dob
    )
    return player

def create_g_league_player(row):
    name = row.find("a").text
    player_url = "https://basketball.realgm.com" + row.find("a")["href"]
    tds = row.find_all("td")
    position = tds[1].text  # Assuming position is in the second td element
    height = tds[2].text  # Assuming height is in the third td element
    weight = tds[3].text  # Assuming weight is in the fourth td element
    school = tds[4].text  # Assuming school is in the fifth td element
    dob = tds[6].text  # Assuming DOB is in the sixth td element

    player = Player(
        name=name, 
        url=player_url,
        position=position, 
        height=height, 
        weight=weight, 
        school=school, 
        dob=dob
    )
    return player

def save_players_to_csv(players):
    if players:
        # Convert the player data to a Pandas DataFrame
        player_data = [player.to_dict() for player in players]
        new_df = pd.DataFrame(player_data)

        # If players.csv exists, load it and append new data
        if os.path.exists("prospects.csv"):
            existing_df = pd.read_csv("prospects.csv")
            existing_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            existing_df = new_df

        # Sort the DataFrame alphabetically by player's name
        if not existing_df.empty:
            existing_df.sort_values('name', inplace=True)

        # Save the DataFrame to a CSV file
        existing_df.to_csv("prospects.csv", index=False)

        # Clear players list
        players = []

def collect_ncaa_data(players):
    # For letter in range alphabet
    for ascii_value in range(ord('A'), ord('Z') + 1):
        letter = chr(ascii_value)
        url = f"https://basketball.realgm.com/ncaa/players/2023/{letter}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = find_target_table(soup)
        rows = table.find_all("tr")

        for i, row in enumerate(rows[1:], 1):
            name = row.find("a").text
            
            if name not in ncaa_prospects:
                continue
            else:
                print(f"Scraping data for {name}...")
                player = create_player(row)
                player.scrape_ncaa_data()
                players.append(player)
    
    return players

def collect_ignite_data(players):
    for name, prospect in ignite_prospects.items():  
        print(f"Scraping data for {name}...")
        player = Player(
            name=prospect['name'], 
            url=prospect['url'],
            position=prospect['Position'], 
            height=prospect['Height'], 
            weight=prospect['Weight'], 
            school=prospect['Pre-Draft Team'], 
            dob=prospect['DOB']
        )
        player.scrape_gleague_data()
        players.append(player)
    
    return players

def collect_international_data(players):
    for name, prospect in int_prospects.items():
        print(f"Scraping data for {prospect['name']}...")
        player = Player(
            name=prospect['name'], 
            url=prospect['url'],
            position=prospect['Position'], 
            height=prospect['Height'], 
            weight=prospect['Weight'], 
            school=prospect['Pre-Draft Team'], 
            dob=prospect['DOB']
        )
        player.scrape_international_data()
        players.append(player)
    
    return players

def collect_data():
    players = []
    players = collect_international_data(players)
    players = collect_ignite_data(players)
    players = collect_ncaa_data(players)
    
        
    save_players_to_csv(players)

if __name__ == "__main__":
    collect_data()