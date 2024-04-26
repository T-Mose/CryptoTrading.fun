import requests
import time
import webbrowser

# URL to fetch the data
url = "https://client-api-2-74b1891ee9f9.herokuapp.com/coins?offset=0&limit=50&sort=created_timestamp&order=DESC&includeNsfw=false"
 # path_to_chrome = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s" # Your path to chrome
path_to_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome %s"  # Your path to Chrome on Mac

def fetch_new_coins(url, first_run):
    # Read the previously processed mints
    try:
        with open('processed_mints.txt', 'r') as file:
            processed_mints = {line.strip() for line in file}
    except FileNotFoundError:
        processed_mints = set()
        first_run = True  # Set to True if no file exists, indicating first run

    # Make the GET request to the URL
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        new_data = False

        for coin in data:
            if coin['mint'] not in processed_mints:
                # Check Twitter link contains 'twitter.com' and has enough followers
                twitter_check = coin['twitter'] and 'twitter.com' in coin['twitter']
                # Check website link is a valid URL and does not redirect to Twitter or Telegram
                website_check = coin['website'] and coin['website'].startswith('https://')
                website_check = website_check and all(site not in coin['website'] for site in ['twitter.com', 'telegram.org'])
                
                if not first_run and twitter_check and website_check:
                    # Open new tabs if it's not the first run and links are valid
                    pump_fun_link = f"https://pump.fun/{coin['mint']}"
                    webbrowser.get(path_to_chrome).open_new_tab(pump_fun_link)
                processed_mints.add(coin['mint'])
                new_data = True

        # Save the new mints back to the file if there was new data
        if new_data:
            with open('processed_mints.txt', 'w') as file:
                for mint in processed_mints:
                    file.write(mint + '\n')
    else:
        print(f"Failed to fetch data: HTTP {response.status_code}")

    return False  # Always return False after the first check

# Initially assume it might be the first run
first_run = True
request_count = 0  # Initialize a counter for the number of requests made

# Infinite loop to keep checking for new coins
while True:
    request_count += 1  # Increment the counter each loop
    print(f"New request {request_count}\n")
    first_run = fetch_new_coins(url, first_run)
    time.sleep(10)  # Wait for 10 seconds before fetching again