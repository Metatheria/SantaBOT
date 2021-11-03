import discord
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import os
import random

from config import Config

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

creds = service_account.Credentials.from_service_account_file(Config.GOOGLE_KEY_FILE, scopes=Config.SHEET_SCOPES) # here enter the name of your downloaded JSON file

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result_input = sheet.values().get(spreadsheetId=Config.SPREADSHEET_ID,
                                range=Config.RANGE_NAME).execute()

names = [line[0] for line in  result_input.get('values', [])]
if Config.HAS_ADDRESS:
    addresses = [line[1] for line in  result_input.get('values', [])]
    messages = [line[2] for line in  result_input.get('values', [])]
else:
    messages = [line[1] for line in  result_input.get('values', [])]

"""
print(names)
print(addresses)
print(messages)
"""

if not names:
    print('No data found.')

n = len(names)

print("This script will send a DM to the " + str(n) + " following people.")
for name in names:
    print(name)

if input("Do you want to proceed?(yes/no)") != "yes":
    print("Aborting")
    sys.exit()

ok = False
while not ok:
    giftees=[i for i in range(n)]
    ok = True
    for i in range(n-1):
        j = random.randint(i,n-1)
        if giftees[j] == i:
            ok = False
            break
        else:
            giftees[i],giftees[j] = giftees[j], giftees[i]
    if giftees[n-1] == n-1:
        ok = False

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    #for m in client.get_all_members():
    #    print(m)
    for i in range(n):
        user = discord.utils.get(client.get_all_members(), name=names[i][:-5], discriminator=names[i][-4:])
        if user is None:
            print("user " + user + " not found")
        else:
            if HAS_ADDRESS:
                await user.send("Your giftee is ||" + names[giftees[i]] + "|| !\n"
                            + "Their address is || " + addresses[giftees[i]] + "||\n"
                            + "They left the following message for you : ||" + messages[giftees[i]] + "||")
            else:
                await user.send("Your giftee is ||" + names[giftees[i]] + "|| !\n"
                            + "They left the following message for you : ||" + messages[giftees[i]] + "||")

    print("Done!")
    await client.close()                             

#ENTER THE TOKEN OF YOUR DISCORD BOT HERE
client.run(Config.DISCORD_BOT_TOKEN)

