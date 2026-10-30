#!/usr/bin/env python3
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------
# Database & Model Setup
# ---------------------------
Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    age = Column(Integer)
    height = Column(String)
    weight = Column(String)
    school = Column(String)
    position = Column(String)
    url = Column(String)  # e.g. RealGM URL
    nba_data = Column(Text)
    nba_awards = Column(Text)
    all_star_selections = Column(Text)
    rating = Column(Integer)  # 2K rating


def setup_database(db_url="sqlite:///players.db"):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------
# Helper Functions
# ---------------------------
headers = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/89.0.4389.82 Safari/537.36')
}


def parse_name(name):
    """
    Parse a player's name into first name, last name, and (optional) suffix.
    E.g. "A.J. Griffin, Jr." → ("A.J.", "Griffin", "Jr.")
    """
    if ',' in name:
        main_part, suffix = name.split(',', 1)
        suffix = suffix.strip()
    else:
        main_part, suffix = name.strip(), ""
    parts = main_part.split()
    if not parts:
        return "", "", suffix
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    return first, last, suffix


def generate_ratings_url(first, last, suffix):
    """
    Generate a URL in the style of your Ruby code.
    Removes dots, lowercases, and concatenates first and last name.
    If a suffix exists, appends it (after removing dots).
    """
    base = "https://www.2kratings.com/"
    first_clean = first.replace('.', '').lower()
    last_clean = last.replace('.', '').lower()
    url = f"{base}{first_clean}-{last_clean}"
    if suffix:
        suffix_clean = suffix.replace('.', '').lower()
        url += "-" + suffix_clean
    return url


def fetch_player_rating(url):
    """
    Fetch the 2K rating from the given URL.
    Looks for an element with class "attribute-box-player" and converts its text to an integer.
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch {url} (status code {response.status_code})")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        rating_elem = soup.find(class_="attribute-box-player")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            try:
                rating = int(rating_text)
                return rating
            except ValueError:
                print(f"Could not convert rating '{rating_text}' to integer for URL {url}")
                return None
        else:
            print(f"Rating element not found for URL {url}")
            return None
    except Exception as e:
        print(f"Exception while fetching rating from {url}: {e}")
        return None


# ---------------------------
# Data Import & Update Routines
# ---------------------------
def import_players_from_csv(csv_path, session):
    """
    Load the cleaned CSV (which contains your RealGM data) and create Player records.
    """
    if not os.path.exists(csv_path):
        print(f"CSV file {csv_path} not found.")
        return
    df = pd.read_csv(csv_path)
    for idx, row in df.iterrows():
        name = row['name']
        # Skip if already imported
        if session.query(Player).filter_by(name=name).first():
            continue
        player = Player(
            name=name,
            age=row.get('age'),
            height=row.get('height'),
            weight=row.get('weight'),
            school=row.get('school'),
            position=row.get('position'),
            url=row.get('url'),
            nba_data=row.get('nba_data'),
            nba_awards=row.get('nba_awards'),
            all_star_selections=row.get('all_star_selections'),
            rating=None  # To be updated from 2K ratings
        )
        session.add(player)
    session.commit()
    print("Imported players from CSV into SQL database.")


def update_ratings(session):
    """
    For every player in the database, generate their 2K ratings URL,
    fetch the current rating, and update the database record.
    """
    players = session.query(Player).all()
    for player in players:
        first, last, suffix = parse_name(player.name)
        ratings_url = generate_ratings_url(first, last, suffix)
        print(f"Fetching rating for {player.name} from {ratings_url}...")
        rating = fetch_player_rating(ratings_url)
        if rating is not None:
            player.rating = rating
            print(f"Updated {player.name} with rating {rating}.")
        else:
            print(f"Could not update rating for {player.name}.")
        session.commit()

# ---------------------------
# Main Routine
# ---------------------------
def main():
    session = setup_database()
    csv_path = "./data/database/clean/cleaned_player_data.csv"  # Path to your cleaned CSV file
    import_players_from_csv(csv_path, session)
    update_ratings(session)
    print("All players updated.")

if __name__ == "__main__":
    main()
