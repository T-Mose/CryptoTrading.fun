import requests
import time
import webbrowser

# Global Variables
url = "https://client-api-2-74b1891ee9f9.herokuapp.com/coins?offset=0&limit=50&sort=created_timestamp&order=DESC&includeNsfw=false"
#path_to_chrome = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s" # Your path to chrome
path_to_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome %s"  # Path to Chrome on Mac
#path_to_chrome = "/Applications/Google Chrome.app %s" #path to Simons Mac


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
    if response.status_code == 200: # We recived data
        coins = response.json() # Format the data
        for coin in coins: # All the poteinally new coins
            if coin['mint'] not in processed_mints: # All coins that are actually new
                if determine_buy(coin) and not first_run:
                    handle_bought_coin(coin)
                processed_mints.add(coin['mint'])

        # Save new mints to the file
        with open('processed_mints.txt', 'w') as file:
            for mint in processed_mints:
                file.write(mint + '\n')
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

# Main loop
first_run = True
request_count = 0
while True:
    request_count += 1
    print(f"New request {request_count}\n")
    first_run = fetch_coin(url, first_run)
    time.sleep(10)
