import threading
import requests
import time
import webbrowser

# Global Variables
coins_url = "https://client-api-2-74b1891ee9f9.herokuapp.com/coins?offset=0&limit=5&sort=created_timestamp&order=DESC&includeNsfw=false"
path_to_chrome = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s" # Your path to chrome
# path_to_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome %s"  # Path to Chrome on Mac
processed_mints = []  # This list will store the mints of the most recent 50 coins in new to old order
USERNAME = "4afy3nH4jZb3jA4MG1PgUfekkdJJdoTXcBLV6Axev54B" # You accounts username on pump.fun
LAMPORTS_PER_SOL = 1_000_000_000
session = None # Keep a constant session which will significantlly improve the api request timings
num_bought_coins = 0

#Importing Selenium Models
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def setup(url):
    """
    Fetch data from the API for initial setup and update processed mints.
    Initialize the HTTP session for reuse.
    
    :param inUrl: The URL to fetch initial coin data from.
    """
    global session
    session = requests.Session()
    coins = make_web_request(url)
    if coins:
        # Process each coin and update processed_mints
        for coin in coins:
            processed_mints.append(coin['mint'])
    else:
        print("Failed to initialize data.")

def fetch_coin(url):
    """
    Fetches new coins from the API, updates the list of processed mints, and handles buying logic.
    
    :param url: The URL to fetch coin data from.
    :return: Boolean indicating success of data fetch.
    """
    coins = make_web_request(url)
    if coins:
        new_mints = []
        for coin in coins:
            if coin['mint'] in processed_mints:
                break  # Early exit if mint is already processed since both lists are similarly sorted
            new_mints.append(coin['mint'])
            if determine_buy(coin):
                handle_bought_coin(coin)

        # Prepend new mints to keep the list ordered new to old
        processed_mints[:0] = new_mints
        # Keep only the latest 50 entries
        processed_mints[:] = processed_mints[:5]
        return True
    else:
        print("Failed to fetch coin data.")
        return False


def determine_buy(coin):
    # Check Twitter and website criteria
    # In the future check other criteria some of them below:
    # Keeping track of the founder and the fewer prevoiusly created coins are a big up
    # Potentially scraping the website to confirm the same token address
    # Add check if dev has sold
    twitter_check = coin['twitter'] and 'twitter.com' in coin['twitter']
    website_check = coin['website'] and coin['website'].startswith('https://') and all(site not in coin['website'] for site in ['twitter.com', 'telegram.org'])
    return twitter_check and website_check and num_bought_coins < 10

def handle_bought_coin(coin):
    # Placeholder for buy and sell logic
    # Currently, just opens a new tab
    pump_fun_link = f"https://pump.fun/{coin['mint']}"
    webbrowser.get(path_to_chrome).open_new_tab(pump_fun_link)
    """ # Untill it is actually impemented
    num_bought_coins += 1
    # Start a new thread to monitor selling criteria
    bought_market_cap = get_market_cap(coin['mint'])
    sell_thread = threading.Thread(target=monitor_and_sell, args=(coin, time.time(), bought_market_cap))
    sell_thread.start()
    """

def get_market_cap(coin_mint):
    """
    Returns the market cap in SOL for a given coin.
    
    :param coin_mint: The mint identifier for the coin.
    :return: The market cap if available; otherwise, returns None.
    """
    url = f"https://client-api-2-74b1891ee9f9.herokuapp.com/coins/{coin_mint}"
    data = make_web_request(url)
    if data:
        return data['market_cap']
    print("Failed to fetch market cap.")
    return None

def monitor_and_sell(coin, purchase_time, bought_market_cap):
    """
    Continuously monitors a coin to decide if it should be sold.
    """
    # Continue checking until the coin is sold
    while True:
        if should_sell(coin, purchase_time, bought_market_cap):
            handle_sold_coin(coin)
            break  # Exit the loop once the coin is sold
        time.sleep(1)  # Check every 30 seconds, adjust frequency as needed

def should_sell(coin, purchase_time, bought_market_cap):
    """
    Determines if the bought coin should be sold based on criteria.
    """
    current_time = time.time()
    hold_duration = 1800  # Adjust this to your selling criteria
    if (current_time - purchase_time) > hold_duration: # Never hold a coin for more than 30 min
        return True
    current_market_cap = get_market_cap(coin['mint'])
    if (current_market_cap / bought_market_cap) > 2 or (current_market_cap / bought_market_cap) < 0.5: # Sell if we have doubled or halfed
        return True
    if(dev_has_sold(coin)): # Sell if dev has abondoned the project
        return True
    # Add other negative signals as we might discover them
    return False

def dev_has_sold(coin):
    """
    Checks if the developer has sold the specified coin.
    
    :param coin_mint: The mint identifier for the coin.
    :return: Boolean indicating whether the developer has sold any of this coin.
    """
    url = f"https://client-api-2-74b1891ee9f9.herokuapp.com/trades/{coin['mint']}?limit=20&offset=0"
    trades = make_web_request(url)
    if trades:
        for trade in trades:
            if trade['username'] == coin['username'] and not trade['is_buy']:
                return True
    return False

def handle_sold_coin(coin):
    # Actions to perform after a coin is sold.
    # Code to actually sell the coin
    sold = True
    num_bought_coins -= 1

def make_web_request(url, max_retries = 3):
    """ 
    Makes a web request using the initialized session and handles common errors.
    
    :param url: The URL to request.
    :return: The JSON response data if successful, or None if the request fails.
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = session.get(url)
            response.raise_for_status()  # Raises HTTPError for bad requests (4XX, 5XX)
            return response.json()
        except requests.HTTPError as e:
            print(f"HTTP error: {e} - Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Request failed: {e}")
        retry_count += 1
        time.sleep(0)  # Adjust based on the API's rate limiting
    print("Maximum retries reached, failed to fetch data.")
    return None

def main():
    request_count = 0
    setup(coins_url)  # Initial setup to prepare the system
    while True:
        request_count += 1
        print(f"New request {request_count}\n")
        fetch_coin(coins_url)
        time.sleep(0)
        # How often it should run. The website wont ever time-out on 1 sec intervall, but at no sleep it eventually throws HTTP 429


if __name__ == '__main__':

    main()