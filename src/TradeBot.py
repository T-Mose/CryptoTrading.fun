import asyncio
import aiohttp
import os
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables from user_info.env
load_dotenv('user_info.env')

# Your Telegram API ID and hash that is pulled from the encrypted file
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
    """
    Asynchronously sets up and starts a Telegram client session.
    """
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
    """
    Determines whether to buy a coin based on specific criteria.
    
    Checks the coin's Twitter and website validity as well as the number of coins already bought.
    
    :param coin: A dictionary containing details of the coin.
    :return: Boolean indicating whether the coin meets the buying criteria.
    """
    twitter_check = coin['twitter'] and 'twitter.com' in coin['twitter']
    website_check = coin['website'] and coin['website'].startswith('https://') and all(site not in coin['website'] for site in ['twitter.com', 'telegram.org'])
    return twitter_check and website_check and num_bought_coins < 10

async def handle_bought_coin(coin):
    """
    Handles the purchase process for a coin, updates the number of coins bought, and initiates monitoring.
    
    This function fetches the market cap of the coin, sends a buy command via Telegram, 
    and starts an asynchronous task to monitor the coin for selling conditions.
    
    :param coin: A dictionary containing details of the coin to be bought.
    """
    global num_bought_coins  # Declare that we use the global variable
    bought_market_cap = await get_market_cap(coin['mint'])
    print("Bought: " + coin['mint'] + " at the MC: " + str(bought_market_cap))
    num_bought_coins += 1
    await send_telegram_command(coin['mint'], 'buy')
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
    Determines if the bought coin should be sold based on criteria.'

    :return: If the given coin should be sold.
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
    """
    Executes actions required after selling a coin, updates global count, and stops monitoring.
    
    Sends a sell command via Telegram, decrements the count of currently bought coins, 
    and disables the monitoring flag for the specified coin to stop the monitoring thread.
    
    :param coin: A dictionary containing details of the coin that has been sold.
    """
    global num_bought_coins  # Declare that we use the global variable
    await send_telegram_command(coin['mint'], 'sell')
    num_bought_coins -= 1 # Update the number of currently owned coins
    thread_flags[coin['mint']] = False  # Set the flag to False to stop the thread

async def make_web_request(url, max_retries=3):
    """
    Attempts to make an HTTP GET request to the specified URL with retries on failure.
    
    This function tries to fetch data from a given URL using an asynchronous HTTP session. 
    If the request fails due to client or server errors, it retries up to `max_retries` times.
    Each retry is attempted after a 1-second delay.
    
    :param url: The URL to make the web request to.
    :param max_retries: The maximum number of retries if the request fails (default is 3).
    :return: The JSON response as a dictionary if the request is successful, otherwise None.
    """
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
    """
    The main execution function for the cryptocurrency trading bot.

    This function initializes the trading system, then continuously fetches and processes new coin data in an infinite loop.
    It manages request pacing to avoid hitting rate limits (HTTP 429 errors) by pausing for one second between each request.
    
    - Initializes the system by setting up the Telegram client and fetching initial coin data.
    - Enters an infinite loop, making successive API requests to fetch new coin data.
    - Handles each new coin by determining buy eligibility and possibly buying the coin.
    - Ensures a manageable request rate to the API to avoid server-side rate limiting.
    """
    request_count = 0
    await setup(coins_url)  # Initial setup to prepare the system
    while True:
        request_count += 1
        print(f"New request {request_count}\n")
        await fetch_coin(coins_url)
        await asyncio.sleep(1)  # Pause for 1 second
        # How often it should run. The website wont ever time-out on 1 sec intervall, but at no sleep it eventually throws HTTP 429

if __name__ == '__main__':
    asyncio.run(main())  # To indicate that this is a true script?