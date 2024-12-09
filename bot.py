import datetime
from io import BytesIO

import discord
import requests
from discord import app_commands
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
apikey = os.getenv('API_key')

if token is None:
    raise ValueError("No token found! Please make sure your .env file is properly configured.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


#command to check cookies for player
@bot.tree.command(name='cookies', description='Check the amount of cookies given to the house.')
@app_commands.describe(name="The username to check cookies for")
async def cookies(interaction: discord.Interaction, name: str):
    await requestInfo(name, interaction)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()


#create playerdata file
def insert_data(displayname, cookies):
    with open(displayname, "w") as file:
        file.write(f'{cookies}')

#read playerdata file
async def read_data(interaction, displayname, search_value=None):

    with open(displayname, "r") as file:
        
        for line in file:
            record = line.strip()
            
        if search_value and search_value in record[1]:

            await sendmessage(displayname, record, interaction)
            print(f'{displayname} has given {record} cookies to the house.')

        elif not search_value:

            await sendmessage(displayname, record, interaction)
            print(f'{displayname} has given {record} cookies to the house.')

#send embedded message to discord
async def sendmessage(displayname, cookie_count, interaction):

    avatar_url = f"https://mc-heads.net/avatar/{displayname}"

    response = requests.get(avatar_url)
    if response.status_code == 200:
        image_bytes = BytesIO(response.content)

    embed = discord.Embed(
        title=f'{displayname}',
        description=f":cookie: Total cookies: {cookie_count}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="attachment://avatar.png")
    file = discord.File(image_bytes, filename="avatar.png")
    await interaction.response.send_message(embed=embed, file=file)


def get_case_sensitive_filename(file_path):
    # Extract the exact filename from the file path
    filename = os.path.basename(file_path)

    # List all files in the directory
    files_in_directory = os.listdir()

    # Iterate and find the exact case-sensitive filename
    for file in files_in_directory:
        if file.lower() == filename.lower():
            return file  # Return the exact case-sensitive filename

    return None

async def requestInfo(username, interaction):
    global player_uuid
    import requests
    uuid_list = []
    housing_api_key = apikey

    displayname = get_case_sensitive_filename(username)

#check if data of player exists and is updated in the past hour.
    if os.path.exists(username):

        #get file hour
        file_mod_date = os.path.getmtime(username)
        file_date = datetime.datetime.fromtimestamp(file_mod_date)
        file_hour = file_date.hour
        file_day = file_date.day

        if file_hour+1 == 25:
            file_hour_plus = 0
        else:
            file_hour_plus = file_hour+1

        if file_hour-1 == -1:
            file_hour_minus = 24
        else:
            file_hour_minus = file_hour-1

        #get current hour
        current_date = datetime.datetime.now()
        current_hour = current_date.hour
        current_day = current_date.day


        #check what current & file dates are set to
        print(file_hour)
        print(current_hour)
        print(file_hour_plus)
        print(file_hour_minus)

        if current_hour is file_hour or current_hour is file_hour_plus or current_hour is file_hour_minus:
            if current_day is file_day:
                await read_data(interaction, displayname)
                print('not requesting data from API.')
                return


# read housingID's from json file.
    with open('housingIDs.json', 'r') as file:
        data = json.load(file)
    housing_uuids = data['housing_uuids']
    print (housing_uuids)




    cookies_count = 0
    base_housing_endpoint = f"https://api.hypixel.net/player?key={housing_api_key}&name={username}"

    try:
        # Send a GET request to the API
        print('Requesting player data from api...')
        response = requests.get(url=base_housing_endpoint)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract JSON data
            player_data = response.json()

            # Check if player data is available
            if 'player' not in player_data or player_data['player'] is None:
                embed = discord.Embed(
                    description=f"No data found for player: {username}",
                    color=discord.Color.red()
                )
                print(f"No data found for player: {username}")
                await interaction.response.send_message(embed=embed)
                return

            if 'player' in player_data and 'housingMeta' in player_data['player']:

                housing_meta = player_data['player'][
                    'housingMeta']  #getting all the houses that cookies have been given to

                player_uuid = player_data['player']['uuid']  #getting the uuid (thanks genius!)
                display_name = player_data['player']['displayname']

                # Count occurrences of housing UUIDs in given_cookies_XXXX lists
                for key in housing_meta:  #filtering
                    if key.startswith("given_cookies_"):
                        for uuid in housing_uuids:
                            if uuid in housing_meta[key]:
                                if uuid not in uuid_list:
                                    uuid_list.append(uuid)
                                cookies_count += housing_meta[key].count(uuid)

            else:
                embed = discord.Embed(
                    description=f"No data found for player: {username}",
                    color=discord.Color.red()
                )
                print(f"No data found for player: {username}")
                await interaction.response.send_message(embed=embed)
                return
        else:
            embed = discord.Embed(
                description=f"No data found for player: {username}",
                color=discord.Color.red()
            )
            print(f"No data was found for player: {username}")
            await interaction.response.send_message(embed=embed)
            return

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for player {e}")
        return

    cookie_count = f"{cookies_count}"
    print(f'display name : {display_name}, cookie count : {cookie_count}')

    await sendmessage(display_name, cookie_count, interaction)

    #create file with cookie data
    insert_data(display_name, cookie_count)

    print(f'{display_name} has given {cookie_count} cookies to the house.')

bot.run(token)

