import asyncio
import aiohttp
import os
import threading
import requests
import time
import webbrowser
from telethon import TelegramClient, events, sync
from dotenv import load_dotenv

# Load environment variables from user_info.env
load_dotenv('user_info.env')

# Your Telegram API ID and hash
api_id = os.getenv('API_ID', '')  # Default to your_api_id if not set
api_hash = os.getenv('API_HASH', '')
user_name = os.getenv('USER_NAME', '')
phone_number = os.getenv('PHONE_NUMBER', '')
bot_username = 'https://t.me/PlonkBot_bot'

# Global Variables
coins_url = "https://client-api-2-74b1891ee9f9.herokuapp.com/coins?offset=0&limit=5&sort=created_timestamp&order=DESC&includeNsfw=false"
path_to_chrome = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s" # Your path to chrome
processed_mints = []  # This list will store the mints of the most recent 50 coins in new to old order
num_bought_coins = 0
thread_flags = {}

# HTTP session and telegram client
session = None # Keep a constant session which will significantlly improve the api request timings
client = None

async def setup(url):
    """
    Fetch data from the API for initial setup and update processed mints.
    Initialize the HTTP session for reuse.
    
    :param inUrl: The URL to fetch initial coin data from.
    """
    global session, client, num_bought_coins
    session = aiohttp.ClientSession()
    client = await setup_telegram_client()
    coins = await make_web_request(url)
    if coins:
        # Process each coin and update processed_mints
        for coin in coins:
            processed_mints.append(coin['mint'])
    else:
        print("Failed to initialize data.")

# Define the function to set up the Telegram client
async def setup_telegram_client():
    client = TelegramClient('session_name', api_id, api_hash)

    # Start the client and sign in automatically
    await client.start(phone=lambda: phone_number)
    print("Client is started and connected.")
    return client

async def fetch_coin(url):
    """
    Fetches new coins from the API, updates the list of processed mints, and handles buying logic.
    
    :param url: The URL to fetch coin data from.
    :return: Boolean indicating success of data fetch.
    """
    coins = await make_web_request(url)
    if coins:
        new_mints = []
        for coin in coins:
            if coin['mint'] in processed_mints:
                break  # Early exit if mint is already processed since both lists are similarly sorted
            new_mints.append(coin['mint'])
            if determine_buy(coin):
                await handle_bought_coin(coin)

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
    return twitter_check and website_check and num_bought_coins < 1

async def handle_bought_coin(coin):
    global num_bought_coins  # Declare that we use the global variable
    # Placeholder for buy and sell logic
    # Currently, just opens a new tab
    pump_fun_link = f"https://pump.fun/{coin['mint']}"
    # webbrowser.get(path_to_chrome).open_new_tab(pump_fun_link)
    bought_market_cap = await get_market_cap(coin['mint'])
    print("Bought: " + coin['mint'] + " at the MC: " + str(bought_market_cap))
    num_bought_coins += 1
    # Untill it is actually impemented
    await send_telegram_command(coin['mint'], 'buy')
    # Start a new thread to monitor selling criteria
    # thread_flags[coin['mint']] = True
    # sell_thread = threading.Thread(target=monitor_and_sell, args=(coin, time.time(), bought_market_cap))
    # sell_thread.start()
     # Asynchronously monitor and sell the coin using asyncio's task creation
    asyncio.create_task(monitor_and_sell(coin, asyncio.get_running_loop().time(), await get_market_cap(coin['mint'])))

async def get_market_cap(coin_mint):
    """
    Returns the market cap in SOL for a given coin.
    
    :param coin_mint: The mint identifier for the coin.
    :return: The market cap if available; otherwise, returns None.
    """
    url = f"https://client-api-2-74b1891ee9f9.herokuapp.com/coins/{coin_mint}"
    data = await make_web_request(url)
    if data:
        return data['market_cap']
    print("Failed to fetch market cap.")
    return None

async def monitor_and_sell(coin, purchase_time, bought_market_cap):
    """
    Continuously monitors a coin to decide if it should be sold.
    """
    # Continue checking until the coin is sold
    while True:  # Check the flag
        await asyncio.sleep(1)  # Use asyncio.sleep to pause without blocking
        if await should_sell(coin, purchase_time, bought_market_cap):
            await handle_sold_coin(coin)
            break  # Exit the loop once the coin is sold

async def should_sell(coin, purchase_time, bought_market_cap):
    """
    Determines if the bought coin should be sold based on criteria.
    """
    current_time = asyncio.get_running_loop().time()
    current_market_cap = await get_market_cap(coin['mint'])
    hold_duration = 60  # Adjust this to your selling criteria
    if (current_time - purchase_time) > hold_duration: # Never hold a coin for more than 30 min
        print("Sold due to time held, at the price: " + str(current_market_cap))
        return True
    if (current_market_cap / bought_market_cap) > 2 or (current_market_cap / bought_market_cap) < 0.5: # Sell if we have doubled or halfed
        print("Sold due to price change, at the price: " + str(current_market_cap))
        return True
    if(await dev_has_sold(coin)): # Sell if dev has abondoned the project
        print("Sold due dev rugging, at the price: " + str(current_market_cap))
        return True
    # Add other negative signals as we might discover them
    return False

async def dev_has_sold(coin):
    """
    Checks if the developer has sold the specified coin.
    
    :param coin_mint: The mint identifier for the coin.
    :return: Boolean indicating whether the developer has sold any of this coin.
    """
    url = f"https://client-api-2-74b1891ee9f9.herokuapp.com/trades/{coin['mint']}?limit=20&offset=0"
    trades = await make_web_request(url)
    if trades:
        for trade in trades:
            if trade['username'] == coin['username'] and not trade['is_buy']:
                return True
    return False

async def handle_sold_coin(coin):
    global num_bought_coins  # Declare that we use the global variable
    # Actions to perform after a coin is sold.
    # Code to actually sell the coin
    await send_telegram_command(coin['mint'], 'sell')
    num_bought_coins -= 1
    thread_flags[coin['mint']] = False  # Set the flag to False to stop the thread

async def make_web_request(url, max_retries=3):
    retry_count = 0
    while retry_count < max_retries:
        try:
            async with session.get(url) as response:  # Reuse the existing session
                response.raise_for_status()  # Raises HTTPError for bad requests (4XX, 5XX)
                return await response.json()  # Asynchronously read and return the response as JSON
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error: {e.status} - {e.message}")
        except aiohttp.ClientError as e:
            print(f"Request failed: {e}")
        retry_count += 1
        await asyncio.sleep(1)  # Asynchronously wait before retrying (non-blocking)
    
    print("Maximum retries reached, failed to fetch data.")
    return None

async def send_telegram_command(mint_address, command):
    """
    Sends a command to the Telegram bot.
    
    :param mint_address: The mint address of the coin.
    :param command: 'buy' or 'sell'
    """
    await client.start()
    command_text = f'{mint_address}'
    await client.send_message(bot_username, command_text)
    print(f"Sent {command} command for: {mint_address}")

async def main():
    request_count = 0
    await setup(coins_url)  # Initial setup to prepare the system
    while True:
        request_count += 1
        print(f"New request {request_count}\n")
        await fetch_coin(coins_url)
        await asyncio.sleep(1)  # Pause for 1 second
        # How often it should run. The website wont ever time-out on 1 sec intervall, but at no sleep it eventually throws HTTP 429

if __name__ == '__main__':
    asyncio.run(main())  # Proper way to run the main function