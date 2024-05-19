import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime

# Define headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extract_birthdate(soup):
    birthdate = soup.find(text=re.compile("Birth Date")).find_next('td').text.strip()
    return birthdate

def extract_draft_year(soup):
    draft_year = soup.find(text=re.compile("Draft")).find_next('td').text.strip().split()[0]
    return draft_year

# def calculate_draft_age(birthdate, draft_year):
#     from datetime import datetime
#     birthdate = datetime.strptime(birthdate, '%B %d, %Y')
#     draft_year = int(draft_year)
#     draft_age = draft_year - birthdate.year
#     return draft_age

def calculate_age(birthdate):
    date_formats = ["%B %d, %Y", "%b %d, %Y"]  # Add more formats if needed
    for date_format in date_formats:
        try:
            birthdate = datetime.strptime(birthdate, date_format)
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"Date format for {birthdate} not recognized")
    
    today = datetime.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def extract_stats(soup, header_text, data_extractor):
    header = soup.find('h2', text=header_text)
    if header:
        table = header.find_next('table')
        if table:
            rows = table.find_all('tr')[1:]  # skip the header row
            stats = data_extractor(rows)
            return stats
    return []

def scrape_awards(soup):
    awards = {}
    awards_table = soup.find(text=re.compile("Awards")).find_next('table')
    rows = awards_table.find_all('tr')[1:]  # skip the header row

    for row in rows:
        cols = row.find_all('td')
        award_name = cols[0].text.strip()
        years = [year.text.strip() for year in cols[1].find_all('a')]
        awards[award_name] = years

    return awards

def clean_value(value):
    """
    Clean the value by replacing dashes with '0' and removing commas.
    """
    return value.replace('-', '0').replace(',', '')

def extract_per_game_data(rows):
    stats = []
    for row in rows[:-1]:  # Skip the last row
        cols = row.find_all('td')
        team_link = cols[1].find('a')
        team = team_link.text.strip() if team_link else cols[1].text.strip()
        
        season_stats = {
            'season': cols[0].text.strip(),
            'team': team,
            'gp': int(clean_value(cols[3].text.strip())),
            'gs': int(clean_value(cols[4].text.strip())),
            'min': float(clean_value(cols[5].text.strip())),
            'ppg': float(clean_value(cols[6].text.strip())),
            'fgm': float(clean_value(cols[7].text.strip())),
            'fga': float(clean_value(cols[8].text.strip())),
            'fg%': float(clean_value(cols[9].text.strip())),
            '3pm': float(clean_value(cols[10].text.strip())),
            '3pa': float(clean_value(cols[11].text.strip())),
            '3p%': float(clean_value(cols[12].text.strip())),
            'ftm': float(clean_value(cols[13].text.strip())),
            'fta': float(clean_value(cols[14].text.strip())),
            'ft%': float(clean_value(cols[15].text.strip())),
            'orb': float(clean_value(cols[16].text.strip())),
            'drb': float(clean_value(cols[17].text.strip())),
            'trb': float(clean_value(cols[18].text.strip())),
            'ast': float(clean_value(cols[19].text.strip())),
            'stl': float(clean_value(cols[20].text.strip())),
            'blk': float(clean_value(cols[21].text.strip())),
            'tov': float(clean_value(cols[22].text.strip())),
            'pf': float(clean_value(cols[23].text.strip())),
        }
        stats.append(season_stats)
    return stats

def extract_misc_stats_data(rows):
    stats = []
    for row in rows:
        cols = row.find_all('td')
        season_stats = {
            'season': cols[0].text.strip(),
            'team': cols[1].text.strip(),
            'gp': int(clean_value(cols[3].text.strip())),
            'gs': int(clean_value(cols[4].text.strip())),
            'min': float(clean_value(cols[5].text.strip())),
            'pts': float(clean_value(cols[6].text.strip())),
            'trb': float(clean_value(cols[18].text.strip())),
            'ast': float(clean_value(cols[19].text.strip())),
            'stl': float(clean_value(cols[20].text.strip())),
            'blk': float(clean_value(cols[21].text.strip())),
            'tov': float(clean_value(cols[22].text.strip())),
            'pf': float(clean_value(cols[23].text.strip())),
        }
        stats.append(season_stats)
    return stats

def extract_winshares_data(rows):
    stats = []
    for row in rows:
        cols = row.find_all('td')
        season_stats = {
            'ows': float(clean_value(cols[17].text.strip())),
            'dws': float(clean_value(cols[18].text.strip())),
            'ws': float(clean_value(cols[19].text.strip())),
        }
        stats.append(season_stats)
    return stats

def extract_advanced_stats_data(rows):
    stats = []
    for row in rows:
        cols = row.find_all('td')
        season_stats = {
            'season': cols[0].text.strip(),
            'team': cols[1].text.strip(),
            'gp': int(clean_value(cols[3].text.strip())),
            'ts%': float(clean_value(cols[4].text.strip())),
            'efg%': float(clean_value(cols[5].text.strip())),
            'orb%': float(clean_value(cols[6].text.strip())),
            'drb%': float(clean_value(cols[7].text.strip())),
            'trb%': float(clean_value(cols[8].text.strip())),
            'ast%': float(clean_value(cols[9].text.strip())),
            'tov%': float(clean_value(cols[10].text.strip())),
            'stl%': float(clean_value(cols[11].text.strip())),
            'blk%': float(clean_value(cols[12].text.strip())),
            'usg%': float(clean_value(cols[13].text.strip())),
            'ortg': float(clean_value(cols[17].text.strip())),
            'drtg': float(clean_value(cols[18].text.strip())),
            'per': float(clean_value(cols[19].text.strip())),
            # Uncomment and clean the following fields if needed
            # 'ows': float(clean_value(cols[16].text.strip())),
            # 'dws': float(clean_value(cols[17].text.strip())),
            # 'ws': float(clean_value(cols[18].text.strip())),
            # 'ws/48': float(clean_value(cols[19].text.strip())),
            # 'obpm': float(clean_value(cols[20].text.strip())),
            # 'dbpm': float(clean_value(cols[21].text.strip())),
            # 'bpm': float(clean_value(cols[22].text.strip())),
            # 'vorp': float(clean_value(cols[23].text.strip())),
        }
        stats.append(season_stats)
    return stats

def convert_values_to_numeric(data):
    numeric_data = data.copy()
    for key, value in data.items():
        try:
            numeric_data[key] = pd.to_numeric(value)
        except ValueError:
            pass  # If conversion fails, keep the original value
    return numeric_data
