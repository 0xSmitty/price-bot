import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from configparser import RawConfigParser


description = '''Bot for token prices'''

intents = discord.Intents.default()

config = RawConfigParser()
config.read("config.ini")

bot = commands.Bot(command_prefix='!', description=description, intents=intents)
# Get the token address from config
token_address = config['token']['address']
chain_id = config['token']['chain_id']  # e.g., 'ethereum', 'bsc', etc.

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    # Start the price update loop when the bot is ready
    update_token_price.start()

# Add a task loop that runs every 30 seconds
@tasks.loop(seconds=30)
async def update_token_price():
    """Updates the bot's nickname with the current token price from Dexscreener API"""
    print("in loop")
    try:
        # Fetch price data from Dexscreener API
        async with aiohttp.ClientSession() as session:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract the price from the response
                    if data.get('pairs') and len(data['pairs']) > 0:
                        # Get the first pair that matches our chain ID
                        for pair in data['pairs']:
                            if pair.get('chainId') == chain_id:
                                market_cap = pair.get('marketCap')

                                if market_cap:
                                    market_cap_float = float(market_cap)
                                    formatted_cap = f"${market_cap_float / 1_000_000:.1f}M"

                                    # Update the bot's nickname in all guilds
                                    for guild in bot.guilds:
                                        try:
                                            await guild.me.edit(nick=formatted_cap)
                                            print(f"Updated nickname to {formatted_cap} in {guild.name}")
                                        except discord.Forbidden:
                                            print(f"Missing permissions to change nickname in {guild.name}")
                                    break
                    else:
                        print("No price data found in the API response")
                else:
                    print(f"Failed to fetch price data: {response.status}")
    except Exception as e:
        print(f"Error updating token price: {e}")

# Wait until the bot is ready before starting the task
@update_token_price.before_loop
async def before_update_token_price():
    await bot.wait_until_ready()

async def main():
    async with bot:
        await bot.start(config['discord']['token'])

asyncio.run(main())