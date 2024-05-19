import requests
import json
from bs4 import BeautifulSoup
from helpers.extraction_helpers import *
from helpers.non_ncaa_extraction_helpers import *
from datetime import datetime

headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36' }

class Player:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        # self.draft_pick = kwargs.get('pick', 0)
        self.url = kwargs.get('url', '')
        self.height = kwargs.get('height')
        self.weight = kwargs.get('weight')
        self.school = kwargs.get('school')
        self.position = kwargs.get('position')
        self.dob = kwargs.get('dob')
        self.draft_age = calculate_age(self.dob)
        self.draft_class = 2024
        self.data = None
        self.seasons = []
        self.nba_seasons = []
        self.nba_awards = []
        self.ncaa_awards = []
        

    def scrape_ncaa_data(self):
        print(f"Scraping {self.name}'s NCAA data...")
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the birthdate and draft year
        # birthdate_str = extract_birthdate(soup)
        # draft_year = extract_draft_year(soup)
        
        # Calculate and set the age at draft
        # self.draft_age = calculate_draft_age(birthdate_str, draft_year)
        
        # Find the NCAA stat tables   
        per_game_rows = extract_stats(soup, 'NCAA Season Stats - Per Game', extract_per_game_data)        
        # misc_stats_rows = extract_stats(soup, 'NCAA Season Stats - Totals', extract_misc_stats_data)
        winshares_rows = extract_stats(soup, 'NCAA Season Stats - Misc Stats', extract_winshares_data)
        advanced_stats_rows = extract_stats(soup, 'NCAA Season Stats - Advanced Stats', extract_advanced_stats_data)
        
        # Scrape NCAA accolades
        # ncaa_awards = scrape_awards(soup, 'NCAA Awards & Honors')
        # self.ncaa_awards = json.dumps(ncaa_awards)
        
        for per_game_data, winshares_data, advanced_stats_data in zip(per_game_rows, winshares_rows, advanced_stats_rows):
            # Combine data from each row
            season_data = {**per_game_data, **winshares_data, **advanced_stats_data}

            # Convert values to numeric
            season_data = convert_values_to_numeric(season_data)
            self.seasons.append(season_data)
    
    def scrape_gleague_data(self):
        print(f"Scraping {self.name}'s G-League Ignite data...")
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        per_game_rows = extract_stats(soup, 'G League Regular Season Stats - Per Game', non_ncaa_extract_per_game_data)        
        # misc_stats_rows = extract_stats(soup, 'G League Regular Season Stats - Totals', non_ncaa_extract_misc_stats_data)
        winshares_rows = extract_stats(soup, 'G League Regular Season Stats - Misc Stats', non_ncaa_extract_winshares_data)
        advanced_stats_rows = extract_stats(soup, 'G League Regular Season Stats - Advanced Stats', non_ncaa_extract_advanced_stats_data)
        
        for per_game_data, winshares_data, advanced_stats_data in zip(per_game_rows, winshares_rows, advanced_stats_rows):
            season_data = {**per_game_data, **winshares_data, **advanced_stats_data}
            season_data = convert_values_to_numeric(season_data)
            self.seasons.append(season_data)
    
    def scrape_international_data(self):
        print(f"Scraping {self.name}'s International data...")
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        per_game_rows = extract_stats(soup, 'International Regular Season Stats - Per Game', extract_per_game_data)        
        # misc_stats_rows = extract_stats(soup, 'International Regular Season Stats - Totals', extract_misc_stats_data)
        winshares_rows = extract_stats(soup, 'International Regular Season Stats - Misc Stats', extract_winshares_data)
        advanced_stats_rows = extract_stats(soup, 'International Regular Season Stats - Advanced Stats', extract_advanced_stats_data)
        
        for per_game_data, winshares_data, advanced_stats_data in zip(per_game_rows, winshares_rows, advanced_stats_rows):
            season_data = {**per_game_data, **winshares_data, **advanced_stats_data}
            season_data = convert_values_to_numeric(season_data)
            self.seasons.append(season_data)
            
    
    def scrape_nba_data(self):
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        nba_per_game_rows = extract_stats(soup, 'NBA Regular Season Stats - Per Game', extract_per_game_data, 'NBA')
        nba_misc_stats_rows = extract_stats(soup, 'NBA Regular Season Stats - Misc Stats', extract_misc_stats_data)
        nba_advanced_stats_rows = extract_stats(soup, 'NBA Regular Season Stats - Advanced Stats', extract_advanced_stats_data)
        
        # Scrape NBA accolades
        nba_awards = scrape_awards(soup, 'NBA Awards & Honors')
        all_star_selections = scrape_awards(soup, 'NBA All-Star Weekend Competitions')
        self.nba_awards = json.dumps(nba_awards)
        self.all_star_selections = json.dumps(all_star_selections)

        for per_game_data, misc_stats_data, advanced_stats_data in zip(nba_per_game_rows, nba_misc_stats_rows, nba_advanced_stats_rows):
            # Combine data from each row
            nba_season_data = {**per_game_data, **misc_stats_data, **advanced_stats_data}

            # Convert values to numeric
            nba_season_data = convert_values_to_numeric(nba_season_data)
            self.nba_seasons.append(nba_season_data)

    
    def to_dict(self):
        return {
            'name': self.name,
            # 'draft_pick': process_draft_pick(self.draft_pick),
            'draft_age': self.draft_age,
            'draft_class': int(self.draft_class),
            'height': self.height,
            'weight': self.weight,
            'school': self.school,
            'position': self.position,
            'url': self.url,
            'ncaa_data': self.seasons,
            'ncaa_awards': self.ncaa_awards,
            'nba_data': self.nba_seasons,
            'nba_awards': self.nba_awards,
        }

           
