import requests
import time
import webbrowser

# Global Variables
url = "https://client-api-2-74b1891ee9f9.herokuapp.com/coins?offset=0&limit=50&sort=created_timestamp&order=DESC&includeNsfw=false"
path_to_chrome = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s" # Your path to chrome
# path_to_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome %s"  # Path to Chrome on Mac

def fetch_coin(url, first_run):
    # Handle file reading for processed mints
    try:
        with open('processed_mints.txt', 'r') as file:
            processed_mints = {line.strip() for line in file}
    except FileNotFoundError:
        processed_mints = set()
        # first_run = True

    # Fetch data from the API
    response = requests.get(url)
    if response.status_code == 200:
        new_mints = []
        coins = response.json()

        for coin in coins:
            if coin['mint'] in processed_mints:
                break  # Early exit if mint is already processed since both list are similarly sorted
            new_mints.append(coin['mint'])
            if determine_buy(coin):
                handle_bought_coin(coin)

        # Prepend new mints to keep the list ordered new to old
        processed_mints[:0] = new_mints
        # Keep only the latest 50 entries
        processed_mints[:] = processed_mints[:50]

    else:
        print(f"Failed to fetch data: HTTP {response.status_code}")
    return False

def determine_buy(coin):
    # Check Twitter and website criteria
    # In the future check other criteria some of them below:
    # Keeping track of the founder and the fewer prevoiusly created coins are a big up
    # Potentially scraping the website to confirm the same token address
    twitter_check = coin['twitter'] and 'twitter.com' in coin['twitter']
    website_check = coin['website'] and coin['website'].startswith('https://') and all(site not in coin['website'] for site in ['twitter.com', 'telegram.org'])
    return twitter_check and website_check

def handle_bought_coin(coin):
    # Placeholder for buy and sell logic
    # Currently, just opens a new tab
    pump_fun_link = f"https://pump.fun/{coin['mint']}"
    webbrowser.get(path_to_chrome).open_new_tab(pump_fun_link)

def main():
    request_count = 0
    setup(url)  # Initial setup to prepare the system
    while True:
        request_count += 1
        print(f"New request {request_count}\n")
        fetch_coin(url)
        time.sleep(0)
        # How often it should run. The website wont ever time-out on 1 sec intervall, but at no sleep it eventually throws HTTP 429

if __name__ == '__main__':
    main()