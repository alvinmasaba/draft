def clean_value(value):
    """
    Clean the value by replacing dashes with '0' and removing commas.
    """
    return value.replace('-', '0').replace(',', '')

def non_ncaa_extract_per_game_data(rows):
    stats = []
    for row in rows[:-1]:  # Skip the last row
        cols = row.find_all('td')
        team_link = cols[0].find('a')
        team = team_link.text.strip() if team_link else cols[0].text.strip()
        
        season_stats = {
            'season': cols[0].text.strip(),
            'team': team,
            'gp': int(clean_value(cols[2].text.strip())),
            'gs': int(clean_value(cols[3].text.strip())),
            'min': float(clean_value(cols[4].text.strip())),
            'ppg': float(clean_value(cols[5].text.strip())),
            'fgm': float(clean_value(cols[6].text.strip())),
            'fga': float(clean_value(cols[7].text.strip())),
            'fg%': float(clean_value(cols[8].text.strip())),
            '3pm': float(clean_value(cols[9].text.strip())),
            '3pa': float(clean_value(cols[10].text.strip())),
            '3p%': float(clean_value(cols[11].text.strip())),
            'ftm': float(clean_value(cols[12].text.strip())),
            'fta': float(clean_value(cols[13].text.strip())),
            'ft%': float(clean_value(cols[14].text.strip())),
            'orb': float(clean_value(cols[15].text.strip())),
            'drb': float(clean_value(cols[16].text.strip())),
            'trb': float(clean_value(cols[17].text.strip())),
            'ast': float(clean_value(cols[18].text.strip())),
            'stl': float(clean_value(cols[19].text.strip())),
            'blk': float(clean_value(cols[20].text.strip())),
            'tov': float(clean_value(cols[21].text.strip())),
            'pf': float(clean_value(cols[22].text.strip())),
        }
        stats.append(season_stats)
    return stats

def non_ncaa_extract_misc_stats_data(rows):
    stats = []
    for row in rows:
        cols = row.find_all('td')
        season_stats = {
            'season': cols[0].text.strip(),
            'team': cols[1].text.strip(),
            'gp': int(clean_value(cols[2].text.strip())),
            'gs': int(clean_value(cols[3].text.strip())),
            'min': float(clean_value(cols[4].text.strip())),
            'pts': float(clean_value(cols[5].text.strip())),
            'trb': float(clean_value(cols[17].text.strip())),
            'ast': float(clean_value(cols[18].text.strip())),
            'stl': float(clean_value(cols[19].text.strip())),
            'blk': float(clean_value(cols[20].text.strip())),
            'tov': float(clean_value(cols[21].text.strip())),
            'pf': float(clean_value(cols[22].text.strip())),
        }
        stats.append(season_stats)
    return stats

def non_ncaa_extract_advanced_stats_data(rows):
    stats = []
    for row in rows:
        cols = row.find_all('td')
        season_stats = {
            'season': cols[0].text.strip(),
            'team': cols[1].text.strip(),
            'gp': int(clean_value(cols[2].text.strip())),
            'ts%': float(clean_value(cols[3].text.strip())),
            'efg%': float(clean_value(cols[4].text.strip())),
            'orb%': float(clean_value(cols[5].text.strip())),
            'drb%': float(clean_value(cols[6].text.strip())),
            'trb%': float(clean_value(cols[7].text.strip())),
            'ast%': float(clean_value(cols[8].text.strip())),
            'tov%': float(clean_value(cols[9].text.strip())),
            'stl%': float(clean_value(cols[10].text.strip())),
            'blk%': float(clean_value(cols[11].text.strip())),
            'usg%': float(clean_value(cols[12].text.strip())),
            'ortg': float(clean_value(cols[16].text.strip())),
            'drtg': float(clean_value(cols[17].text.strip())),
            'per': float(clean_value(cols[18].text.strip())),
            # Uncomment and clean the following fields if needed
            # 'ows': float(clean_value(cols[15].text.strip())),
            # 'dws': float(clean_value(cols[16].text.strip())),
            # 'ws': float(clean_value(cols[17].text.strip())),
            # 'ws/48': float(clean_value(cols[18].text.strip())),
            # 'obpm': float(clean_value(cols[19].text.strip())),
            # 'dbpm': float(clean_value(cols[20].text.strip())),
            # 'bpm': float(clean_value(cols[21].text.strip())),
            # 'vorp': float(clean_value(cols[22].text.strip())),
        }
        stats.append(season_stats)
    return stats

def non_ncaa_extract_winshares_data(rows):
    stats = []
    for row in rows:
        cols = row.find_all('td')
        season_stats = {
            'ows': float(clean_value(cols[16].text.strip())),
            'dws': float(clean_value(cols[17].text.strip())),
            'ws': float(clean_value(cols[18].text.strip())),
        }
        stats.append(season_stats)
    return stats