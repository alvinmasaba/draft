import subprocess

def main():
    # Run the data collection script
    print("Starting Data Collection...")
    try:
        subprocess.run(["python3", "data_collection.py"], check=True)
        print("Data Collection Complete.")
    except subprocess.CalledProcessError as e:
        print("Error during data collection:", e)
        return

    # Run the data cleaning script
    print("Starting Data Cleaning...")
    try:
        subprocess.run(["python3", "data_cleaning.py"], check=True)
        print("Data Cleaning Complete.")
    except subprocess.CalledProcessError as e:
        print("Error during data cleaning:", e)
        return

if __name__ == "__main__":
    main()
