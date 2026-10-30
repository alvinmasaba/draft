import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import numpy as np

# Define headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extract_birthdate(soup):
    """
    Extracts the birthdate from the player's profile page.
    """
    # Look for the "Born:" text in any tag
    born_tag = soup.find(string=lambda text: text and "Born:" in text)
    
    if born_tag:
        # Find the parent tag of the "Born:" text
        parent_tag = born_tag.find_parent()
        
        # Extract the birthdate from the next sibling or within the same tag
        birthdate = None
        if parent_tag:
            # Check if the birthdate is in a sibling tag
            sibling = parent_tag.find_next_sibling()
            if sibling:
                birthdate = sibling.get_text(strip=True)
            else:
                # If no sibling, check if the birthdate is in the same tag
                birthdate = parent_tag.get_text(strip=True).replace("Born:", "").strip()
        
        if birthdate:
            # print(f"Extracted birthdate: {birthdate}")
            return birthdate
    
    print("Birthdate not found.")
    return None


def extract_draft_year(soup):
    draft_year = soup.find(text=re.compile("Draft")).find_next('td').text.strip().split()[0]
    return draft_year


def calculate_draft_age(birthdate, draft_year):
    from datetime import datetime
    birthdate = datetime.strptime(birthdate, '%B %d, %Y')
    draft_year = int(draft_year)
    draft_age = draft_year - birthdate.year
    return draft_age


def calculate_age(birthdate):
    """
    Calculates the age of a player given their birthdate.
    Handles both full and abbreviated month formats.
    """
    date_formats = [
        "%b %d, %Y",  # Abbreviated month name (e.g., "Sep 19, 1999")
        "%B %d, %Y",  # Full month name (e.g., "September 19, 1999")
        "%Y-%m-%d",   # ISO format (e.g., "1999-09-19")
    ]
    
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

import json


def extract_stats(soup, header_text, data_extractor):
    """
    Extracts statistical data from the first table following a given <h3> header.
    Now includes debugging output.
    """
    header = soup.find('h3', string=lambda text: text and header_text in text)

    if header:
        # print(f"\n✅ Found header: {header_text}")

        # Find the table associated with this header
        table = header.find_next('table')

        if table:
            # print(f"📊 Table found for {header_text}\n")

            # # Pretty-print full table HTML
            # print("\n=== FULL TABLE HTML ===")
            # print(table.prettify())  # Debugging full table output

            # Print header row for verification
            # thead = table.find('thead')
            # if thead:
            #     print("\n=== TABLE HEADER ===")
            #     print(thead.prettify())  # Debugging header output

            # Extract rows (excluding header row)
            rows = table.find_all('tr')[1:]  

            stats = data_extractor(rows)

            # # Pretty-print extracted JSON stats
            # print("\n=== EXTRACTED STATS JSON ===")
            # print(json.dumps(stats, indent=4))  # Final output for verification

            return stats
        else:
            print(f"❌ Table NOT found for {header_text}")
    else:
        print(f"❌ Header NOT found: {header_text}")

    return []



def scrape_awards(soup, header_text):
    """
    Scrapes awards and honors from the player's profile page.
    Extracts both the award name and the years/dates.
    """
    awards = {}
    
    # Find the awards section by header text
    awards_header = soup.find('h3', string=lambda text: text and header_text in text)
    
    if awards_header:
        awards_table = awards_header.find_next('table')
        rows = awards_table.find_all('tr')[1:]  # Skip the header row

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:  # Ensure there are at least 2 columns
                award_name = cols[0].text.strip()  # Extract award name from the first column
                years = [year.text.strip() for year in cols[1].find_all('a')]  # Extract years/dates from the second column
                awards[award_name] = years
    
    return awards


def scrape_nba_awards(soup):
    """
    Scrapes the NBA Awards & Honors table from the player page.
    It looks for an <h3> element whose text includes the word 'Awards'.
    """
    
    # Use a looser match to catch any header with "Award" in it
    header = soup.find("h3", string=lambda text: text and "Award" in text)
    awards = {}
    if header:
        table = header.find_next("table")
        if table:
            for row in table.find_all("tr"):
                cell = row.find("td")
                if cell:
                    # Get the award name (try the <strong> with <a> if available)
                    strong = cell.find("strong")
                    if strong and strong.a:
                        award_name = strong.a.get_text(strip=True)
                    else:
                        # Fallback: use text before the dash
                        award_name = cell.get_text(strip=True).split(" - ")[0]
                    # Extract years (if any) after the dash
                    parts = cell.get_text(separator=" ", strip=True).split(" - ")
                    years = [year.strip() for year in parts[1].split(",")] if len(parts) > 1 else []
                    awards[award_name] = years
        else:
            print("Awards table not found after header:", header.get_text(strip=True))
    else:
        print("No header containing 'Award' was found.")
    return awards


def scrape_nba_all_star_awards(soup, header_text):
    """
    Scrapes NBA All-Star appearances and awards.
    """
    all_star_awards = {}

    awards_header = soup.find('h3', string=lambda text: text and header_text in text)

    if awards_header:
        awards_table = awards_header.find_next('table')

        if awards_table:
            rows = awards_table.find_all('tr')

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 1:
                    award_name_tag = cols[0].find('a')
                    award_name = award_name_tag.text.strip() if award_name_tag else cols[0].text.strip()

                    # Extract years from multiple <a> tags inside the <td>
                    years_list = [year.text.strip() for year in cols[0].find_all('a')]

                    all_star_awards[award_name] = years_list

    return all_star_awards


def clean_value(value):
    """
    Clean the value by replacing dashes with '0' and removing commas.
    """
    return value.replace('-', '0').replace(',', '')


def extract_per_game_data(rows):
    data = []
    for idx, row in enumerate(rows):
        cols = row.find_all('td')

        # Debugging: Print row index and number of columns found
        # print(f"\n🔍 Processing row {idx}: Found {len(cols)} columns")

        if len(cols) < 2:
            print(f"⚠️ Skipping row {idx} due to insufficient columns: {len(cols)}")
            continue

        # Extract season
        season = cols[0].text.strip()

        # Handle cases where the team column might be missing an <a> tag
        team = cols[1].text.strip()
        team_link = cols[1].find('a')
        if team_link:
            team = team_link.text.strip()  # Use link text if available

        # Extract stats and log each extraction
        try:
            player_stats = {
                "season": season,
                "team": team,
                "age": cols[2].text.strip(),
                "gp": cols[3].text.strip(),
                "gs": cols[4].text.strip(),
                "min": cols[5].text.strip(),
                "pts": cols[6].text.strip(),
                "fgm": cols[7].text.strip(),
                "fga": cols[8].text.strip(),
                "fg_pct": cols[9].text.strip(),
                "3pm": cols[10].text.strip(),
                "3pa": cols[11].text.strip(),
                "3p_pct": cols[12].text.strip(),
                "ftm": cols[13].text.strip(),
                "fta": cols[14].text.strip(),
                "ft_pct": cols[15].text.strip(),
                "off": cols[16].text.strip(),
                "def": cols[17].text.strip(),
                "trb": cols[18].text.strip(),
                "ast": cols[19].text.strip(),
                "stl": cols[20].text.strip(),
                "blk": cols[21].text.strip(),
                "tov": cols[22].text.strip(),
                "pf": cols[23].text.strip(),
            }

            # Debugging: Print extracted values
            # print(f"📌 Extracted stats for {season}: {json.dumps(player_stats, indent=4)}")

        except IndexError as e:
            print(f"⚠️ Skipping row {idx} due to missing columns. Error: {e}")
            continue  # Skip this row and move to the next

        data.append(player_stats)

    return data


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


def convert_values_to_python(data):
    """Converts NumPy data types to native Python types for JSON serialization."""
    clean_data = {}
    for key, value in data.items():
        if isinstance(value, (np.int64, np.float64)):
            clean_data[key] = value.item()  # Convert to native int/float
        elif isinstance(value, float) and np.isnan(value):
            clean_data[key] = None  # Convert NaN to None
        else:
            clean_data[key] = value
    return clean_data