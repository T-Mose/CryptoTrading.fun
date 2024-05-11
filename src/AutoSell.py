from telethon import TelegramClient, events, sync

# Your Telegram API ID and hash (replace these with your actual values)
api_id = 'your_api_id'
api_hash = 'your_api_hash'
#The username of the Telegram bot to which commands are sent
bot_username = 'bot_username'

#Create and start the Telegram client session
client = TelegramClient('anon', api_id, api_hash)

async def send_buy_command(mint_address):
    """
    Sends a buy command to a specific Telegram bot.

    :param mint_address: The mint address of the coin to buy.
    """
    await client.start()
    await client.send_message(bot_username, f'/sell {mint_address}')
    print(f"Sent buy command for: {mint_address}")

def buy_coin(coin_mint):
    """
    Initiates the purchase of a coin by sending a command to a Telegram bot.

    :param coin_mint: The unique identifier for the coin to be bought.
    """
    print(f"Attempting to buy coin with mint address: {coin_mint}")
    # Running the async function using the Telethon client's event loop
    client.loop.run_until_complete(send_buy_command(coin_mint))

#Example usage and test; comment this out when using this script as a module
#buy_coin('123abc456def')

#tedde6489
#tedde6489

