import requests
import json
from bs4 import BeautifulSoup
from helpers.extraction_helpers import *
from helpers.non_ncaa_extraction_helpers import *
from datetime import datetime
import sys

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/89.0.4389.82 Safari/537.36'
}

class Player:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.url = kwargs.get('url', '')
        self.height = kwargs.get('height')
        self.weight = kwargs.get('weight')
        self.school = kwargs.get('school')
        self.position = kwargs.get('position')
        self.pick = kwargs.get('pick')
        self.draft_class = 2024
        self.nba_seasons = []
        self.nba_awards = ""
        self.all_star_selections = ""
        self.current_age = None
        self.rating_2k = None          # New field for current 2K rating
        self.historical_ratings = {}   # New field for historical ratings (a dict)
        self.wingspan = None           # New field for wingspan (in inches)
        self.archetype = None          # New field for archetype

    def scrape_nba_data(self):
        print(f"Scraping NBA data for {self.name} from {self.url}")
        response = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract birthdate and calculate current age
        birthdate_str = extract_birthdate(soup)
        self.current_age = calculate_age(birthdate_str)
        
        # --- NEW: Extract wingspan and archetype from the RealGM page ---
        info_paragraphs = soup.find_all("p", class_="mb-1 my-lg-0")
        for p in info_paragraphs:
            text = p.get_text()
            if "Wingspan:" in text:
                wingspan_span = p.find("span", class_="text-light")
                if wingspan_span:
                    self.wingspan = convert_wingspan_to_inches(wingspan_span.get_text(strip=True))
            if "Archetype:" in text:
                archetype_span = p.find("span", class_="text-light")
                if archetype_span:
                    self.archetype = archetype_span.get_text(strip=True)
        # --- End new extraction ---
        
        nba_per_game_rows = extract_stats(soup, 'NBA Regular Season Stats - Per Game', extract_per_game_data)
        nba_misc_stats_rows = extract_stats(soup, 'NBA Regular Season Stats - Misc Stats', extract_winshares_data)
        nba_advanced_stats_rows = extract_stats(soup, 'NBA Regular Season Stats - Advanced Stats', extract_advanced_stats_data)

        nba_awards = scrape_nba_awards(soup)
        nba_all_stars = scrape_nba_all_star_awards(soup, 'NBA All-Star Weekend Competitions')

        self.nba_awards = json.dumps(nba_awards)
        self.all_star_selections = json.dumps(nba_all_stars)
        
        if not nba_per_game_rows:
            print(f"Warning: No NBA per game stats found for {self.name}")

        for per_game_data, misc_stats_data, advanced_stats_data in zip(nba_per_game_rows, nba_misc_stats_rows, nba_advanced_stats_rows):
            nba_season_data = {**per_game_data, **misc_stats_data, **advanced_stats_data}
            nba_season_data = convert_values_to_numeric(nba_season_data)
            cleaned_stats = convert_values_to_python(nba_season_data)  
            self.nba_seasons.append(cleaned_stats)
    
    def scrape_2kratings_data(self):
        """
        Uses undetected-chromedriver in headless mode to fetch the player's
        NBA 2K rating data from 2kratings.com. This method retrieves both the
        current rating and a table of historical ratings.
        """
        print(f"Scraping 2K Ratings data for {self.name}...")
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except ImportError as e:
            print("Error: undetected_chromedriver module not installed.", e)
            return
        
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        
        driver = None
        try:
            driver = uc.Chrome(options=options)
            # Construct the 2KRatings URL based on the player's name.
            slug = self.name.lower().replace(" ", "-")
            ratings_url = f"https://www.2kratings.com/{slug}"
            print("Navigating to URL:", ratings_url)
            driver.get(ratings_url)
            
            # Wait until the rating element appears (adjust the XPath if necessary)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'attribute-box')]"))
            )
            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'html.parser')
            # Get current rating from the element with class "attribute-box player"
            rating_element = soup.find('span', class_='attribute-box player')
            if rating_element:
                self.rating_2k = rating_element.get_text(strip=True)
                print(f"Current 2K Rating for {self.name} is: {self.rating_2k}")
            else:
                print(f"Current rating element not found for {self.name}.")
                self.rating_2k = None

            # Now parse the historical ratings table.
            historical_ratings = {}
            # Look for a <tbody> that contains rows starting with "NBA 2K"
            tbodies = soup.find_all("tbody")
            for tbody in tbodies:
                rows = tbody.find_all("tr")
                if rows and "NBA 2K" in rows[0].get_text():
                    for row in rows:
                        tds = row.find_all("td")
                        if len(tds) >= 2:
                            season_text = tds[0].get_text(strip=True)  # e.g. "NBA 2K21"
                            # Extract the last two digits (e.g. "21")
                            digits = season_text[-2:]
                            if digits.isdigit():
                                y = int(digits)
                                # NBA 2K21 corresponds to the 2020-21 season
                                season_str = f"20{y-1:02d}-20{y}"
                            else:
                                season_str = season_text  # fallback
                            rating_text = tds[1].get_text(strip=True)
                            historical_ratings[season_str] = rating_text
                    break  # Assume we found the correct table
            self.historical_ratings = historical_ratings
            print(f"Historical ratings for {self.name}: {self.historical_ratings}")
        except Exception as e:
            print(f"Error scraping 2K Ratings data for {self.name}:", e)
            self.rating_2k = None
            self.historical_ratings = {}
        finally:
            if driver:
                driver.quit()
    
    def to_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'position': self.position,
            'height': self.height,
            'weight': self.weight,
            'school': self.school,
            'pick': self.pick,
            'age': self.current_age,
            'nba_data': self.nba_seasons,
            'nba_awards': self.nba_awards,
            'all_star_selections': self.all_star_selections,
            'rating_2k': self.rating_2k,
            'historical_ratings': json.dumps(self.historical_ratings) if self.historical_ratings else None,
            'wingspan': self.wingspan,
            'archetype': self.archetype
        }

# Helper function to convert a wingspan string (e.g. "6'9" (206cm)") to inches.
def convert_wingspan_to_inches(wingspan_str):
    if not wingspan_str:
        return None
    # Example expected format: 6'9" (206cm)
    try:
        # Split by space and take the first part ("6'9" or 6'9")
        measurement = wingspan_str.split(" ")[0]
        if "'" in measurement:
            ft, inch = measurement.split("'")
            # Remove any double quotes from the inches part
            inch = inch.replace('"', '')
            return int(ft) * 12 + int(inch)
    except Exception as e:
        print("Error converting wingspan:", e)
    return None




# def scrape_ncaa_data(self):
#     print(f"Scraping {self.name}'s NCAA data...")
#     response = requests.get(self.url, headers=headers)
#     soup = BeautifulSoup(response.text, 'html.parser')
    
#     # Extract the birthdate and draft year
#     birthdate_str = extract_birthdate(soup)
#     draft_year = extract_draft_year(soup)
    
#     # Calculate and set the age at draft
#     # self.draft_age = calculate_draft_age(birthdate_str, draft_year)
#     self.current_age = calculate_age(birthdate_str)
    
#     # Find the NCAA stat tables   
#     per_game_rows = extract_stats(soup, 'NCAA Season Stats - Per Game', extract_per_game_data)        
#     misc_stats_rows = extract_stats(soup, 'NCAA Season Stats - Totals', extract_misc_stats_data)
#     winshares_rows = extract_stats(soup, 'NCAA Season Stats - Misc Stats', extract_winshares_data)
#     advanced_stats_rows = extract_stats(soup, 'NCAA Season Stats - Advanced Stats', extract_advanced_stats_data)
    
#     # Scrape NCAA accolades
#     # ncaa_awards = scrape_awards(soup, 'NCAA Awards & Honors')
#     # self.ncaa_awards = json.dumps(ncaa_awards)
    
#     for per_game_data, winshares_data, advanced_stats_data in zip(per_game_rows, winshares_rows, advanced_stats_rows):
#         # Combine data from each row
#         season_data = {**per_game_data, **winshares_data, **advanced_stats_data}

#         # Convert values to numeric
#         season_data = convert_values_to_numeric(season_data)
#         self.seasons.append(season_data)


# def scrape_gleague_data(self):
#     print(f"Scraping {self.name}'s G-League Ignite data...")
#     response = requests.get(self.url, headers=headers)
#     soup = BeautifulSoup(response.text, 'html.parser')

#     per_game_rows = extract_stats(soup, 'G League Regular Season Stats - Per Game', non_ncaa_extract_per_game_data)        
#     # misc_stats_rows = extract_stats(soup, 'G League Regular Season Stats - Totals', non_ncaa_extract_misc_stats_data)
#     winshares_rows = extract_stats(soup, 'G League Regular Season Stats - Misc Stats', non_ncaa_extract_winshares_data)
#     advanced_stats_rows = extract_stats(soup, 'G League Regular Season Stats - Advanced Stats', non_ncaa_extract_advanced_stats_data)
    
#     for per_game_data, winshares_data, advanced_stats_data in zip(per_game_rows, winshares_rows, advanced_stats_rows):
#         season_data = {**per_game_data, **winshares_data, **advanced_stats_data}
#         season_data = convert_values_to_numeric(season_data)
#         self.seasons.append(season_data)


# def scrape_international_data(self):
#     print(f"Scraping {self.name}'s International data...")
#     response = requests.get(self.url, headers=headers)
#     soup = BeautifulSoup(response.text, 'html.parser')

#     per_game_rows = extract_stats(soup, 'International Regular Season Stats - Per Game', extract_per_game_data)        
#     # misc_stats_rows = extract_stats(soup, 'International Regular Season Stats - Totals', extract_misc_stats_data)
#     winshares_rows = extract_stats(soup, 'International Regular Season Stats - Misc Stats', extract_winshares_data)
#     advanced_stats_rows = extract_stats(soup, 'International Regular Season Stats - Advanced Stats', extract_advanced_stats_data)
    
#     for per_game_data, winshares_data, advanced_stats_data in zip(per_game_rows, winshares_rows, advanced_stats_rows):
#         season_data = {**per_game_data, **winshares_data, **advanced_stats_data}
#         season_data = convert_values_to_numeric(season_data)
#         self.seasons.append(season_data)
            