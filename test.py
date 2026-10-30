import sqlite3

def discount_factor_for_ts(height_in_inches, threshold=82, rate=0.35, min_factor=0.4):
    """
    For players taller than 'threshold' inches, return a discount factor for ts%.
    The factor decreases by (height - threshold)*rate, but will not go below min_factor.
    """
    if height_in_inches <= threshold:
        return 1.0
    else:
        factor = 1 - (height_in_inches - threshold) * rate
        return max(min_factor, factor)

def convert_height_to_inches(height_str):
    """
    Convert a height string in the format "6-9" (feet-inches) into total inches.
    Returns None if conversion fails.
    """
    try:
        parts = height_str.split('-')
        if len(parts) == 2:
            feet = int(parts[0])
            inches = int(parts[1])
            return feet * 12 + inches
    except Exception as e:
        print("Error converting height:", e)
    return None

def test_height_conversion(db_path="players.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, height FROM players")
    players = cursor.fetchall()
    conn.close()

    print(f"{'Player':<30} {'Height String':<15} {'Converted Inches':>18}")
    print("-" * 65)
    for name, height in players:
        if height:
            inches = convert_height_to_inches(height)
        else:
            inches = None
        print(f"{name:<30} {height:<15} {str(inches):>18}")


if __name__ == "__main__":
    # Test discount_factor_for_ts directly
    for test_height in [80, 82, 83, 84, 85, 90]:
        disc = discount_factor_for_ts(test_height, threshold=82, rate=0.55, min_factor=0.4)
        print(f"Height {test_height} inches: discount factor = {disc:.3f}")
