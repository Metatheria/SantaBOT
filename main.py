from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import discord
import random
import sys
import numpy as np

from config import Config
from maxflow import maxflow

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

creds = service_account.Credentials.from_service_account_file(Config.GOOGLE_KEY_FILE, scopes=Config.SHEETS_SCOPES)

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result_input = sheet.values().get(spreadsheetId=Config.SPREADSHEET_ID,
                                range=Config.RANGE_NAME).execute()

#print(result_input.get('values', []))

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
secretMessages = [line[i] for line in  result_input.get('values', [])]


if Config.HAS_CONFLICT_MANAGEMENT:
    i += 1

conflicts = [[names.index(name) for name in (line[i].split(',') if Config.HAS_CONFLICT_MANAGEMENT and len(line) > i else [])] for line in result_input.get('values', [])]

for c in range(n):
    conflicts[c] += [c]
    
print(conflicts)


print("This script will send a DM to the " + str(n) + " following people:")
for name in names:
    print(name)

if Config.DRY_RUN:
    print('[THIS IS A DRY RUN]')

if input("Do you want to proceed?(yes/no)") != "yes":
    print("Aborting...")
    sys.exit()

graph = np.zeros((2*n+2, 2*n+2))
hat = [i for i in range(n)]
giftees = [-1]*n
random.shuffle(hat)
for i in range(n):
    graph[0][i+1] = 1
    graph[n+i+1][2*n+1] = 1
    for j in range(n):
        if j not in conflicts[i]:
            graph[hat[i]+1][n+j+1] = 1

flow = maxflow(graph,0,2*n+1)
if flow < n:
    print("Too many constraints, problem is unsolvable\nAborting...")
    sys.exit()
else:
    message = ["" for _ in range(n)]
    for i in range(n):
        giftees[i] = hat.index(np.where(graph[i+n+1] == 1)[0][0]-1)

        message[i] = f'Your giftee is ||{names[giftees[i]]}|| !\n'
        
        if Config.HAS_ADDRESS:
            message[i] += f'Their address is:\n||{addresses[giftees[i]]}||\n'
        
        if secretMessages[giftees[i]]:
            message[i] += f'They left the following message for you: \n||{secretMessages[giftees[i]]}||\n'
        
        if Config.DRY_RUN:
            print(f'[MESSAGE FOR {names[i]}]')
            print(message)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    #for m in client.get_all_members():
    #    print(m)
    fail = False
    successful_users = []
    for i in range(n):
        user = discord.utils.get(client.get_all_members(), name=names[i][:-5], discriminator=names[i][-4:])
        if user is None:
            print("user " + names[i] + " not found", file=sys.stderr)
            fail = True
        else:
            try:
                await user.send("Matching is about to begin, please wait")
            except:
                print("Could not DM user " + names[i])
                fail = True
            else:
                successful_users+=[user]
    if fail:
        print("Aborting...")
        for u in successful_users:
            await u.send("An error occurred during matching, so it has been aborted.")

    else:
        for i in range(len(successful_users)):
            await successful_users[i].send(message[i])
        print("Done!")
    await client.close()

if not Config.DRY_RUN:
    client.run(Config.DISCORD_BOT_TOKEN)

