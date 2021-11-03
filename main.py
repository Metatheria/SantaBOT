import discord
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import os
import random
import sys

from config import Config

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

creds = service_account.Credentials.from_service_account_file(Config.GOOGLE_KEY_FILE, scopes=Config.SHEETS_SCOPES) # here enter the name of your downloaded JSON file

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result_input = sheet.values().get(spreadsheetId=Config.SPREADSHEET_ID,
                                range=Config.RANGE_NAME).execute()

print(result_input.get('values', []))

i = 0
names = [line[i] for line in  result_input.get('values', [])]

if not names:
    print('No data found.')
    sys.exit(1)

n = len(names)

if Config.HAS_ADDRESS:
    i += 1
    addresses = [line[i] for line in  result_input.get('values', [])]

i += 1
messages = [line[i] for line in  result_input.get('values', [])]

if Config.HAS_CONFLICT_MANAGEMENT:
    i += 1
    conflicts = [[names.index(name) for name in (line[i].split(',') if len(line) > i else [])] for line in result_input.get('values', [])]
    
    for c in range(n):
        conflicts[c] += [c]
    
    print(conflicts)


print("This script will send a DM to the " + str(n) + " following people.")
for name in names:
    print(name)

if Config.DRY_RUN:
    print('[THIS IS A DRY RUN]')

if input("Do you want to proceed?(yes/no)") != "yes":
    print("Aborting")
    sys.exit()


if Config.HAS_CONFLICT_MANAGEMENT:
    # TODO Better algorithm for conflict management
    ok = False
    hat = [i for i in range(n)]
    giftees = [-1] * n

    while not ok:
        ok = True
        hat = sorted(hat, key=lambda x: random.random())
        for i in range(n):
            if hat[(i+1) % n] in conflicts[hat[i]]:
                print(f'conflict: {names[hat[i]]} cannot gift to {names[hat[(i+1)%n]]}, retrying')
                ok = False
                break
    
    for i in range(n):
        giftees[hat[i]] = hat[((i+1) % n)]
    
else:
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
        message = f'Your giftee is ||{names[giftees[i]]}|| !\n'
        
        if Config.HAS_ADDRESS:
            message += f'Their address is:\n||{addresses[giftees[i]]}||\n'
        
        m = messages[giftees[i]]
        if m:
            message += f'They left the following message for you: \n||{messages[giftees[i]]}||\n'

        if Config.DRY_RUN:
            print(f'[MESSAGE FOR {names[i]}]')
            print(message)
        else:
            if user is None:
                print("user " + user + " not found", file=sys.stderr)
                print(message)
            else:
                user.send(message)

    print("Done!")
    await client.close()

#ENTER THE TOKEN OF YOUR DISCORD BOT HERE
client.run(Config.DISCORD_BOT_TOKEN)

