"""Module launching the whole Secret Santa workflow"""

import random
import sys
from googleapiclient.discovery import build
from google.oauth2 import service_account

from config import Config
from discord_client import DiscordClient
from email_client import EmailClient
from maxflow import maxflow

creds = service_account.Credentials.from_service_account_file(
        Config.GOOGLE_KEY_FILE,
        scopes=Config.SHEETS_SCOPES)

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()

ranges = [Config.SHEET_NAME + "!" + column for column in Config.RANGES.values() if column]
response = (sheet.values().batchGet(spreadsheetId=Config.SPREADSHEET_ID,
                                ranges=ranges, majorDimension='COLUMNS').execute())['valueRanges']

results = {}

current_column = 0
for key in Config.RANGES.keys():
    if Config.RANGES[key] and 'values' in response[current_column]:
        results[key] = response[current_column]['values'][0]
        current_column+=1

contacts = results['contact']

if not contacts:
    print('No data found.')
    sys.exit(1)

n = len(contacts)

if Config.RANGES['name']:
    names = results['name']
    if len(names) != n:
        print('Someone has not registered their name')
        sys.exit(1)
else:
    names = results['contact']

if Config.RANGES['address']:
    addresses = results['address']
    if len(addresses) != n:
        print('Someone has not registered their address')
        sys.exit(1)
else:
    addresses = []

if Config.RANGES['mess_to_santa']:
    santa_messages = results['mess_to_santas']
    santa_messages += ['']*(n-len(santa_messages))
else:
    santa_messages = []

print(len(santa_messages))

if Config.RANGES['conflicts']:
    conflicts = [[names.index(name)
                for name in (conflict.split(','))]
                for conflict in results['conflicts']]
    conflicts += [[]]*(n-len(conflicts))
    for c in range(n):
        conflicts[c] += [c]
else:
    conflicts = [[c] for c in range(n)]

print(conflicts)


print(f"This script will send a message to the {n} following people:")
for contact in contacts:
    print(contact)

if Config.DRY_RUN:
    print('[THIS IS A DRY RUN]')

if input("Do you want to proceed?(yes/no)") != "yes":
    print("Aborting...")
    sys.exit()

graph = [[0]*(2*n+2) for _ in range(2*n+2)]
hat = [current_column for current_column in range(n)]
giftees = [-1]*n
random.shuffle(hat)
for current_column in range(n):
    graph[0][current_column+1] = 1
    graph[n+current_column+1][2*n+1] = 1
    for j in range(n):
        if j not in conflicts[current_column]:
            graph[hat[current_column]+1][n+j+1] = 1
flow = maxflow(graph, 0, 2*n+1)
if flow < n:
    print("Too many constraints, problem is unsolvable\nAborting...")
    sys.exit()
else:
    messages = ["" for _ in range(n)]
    for current_column in range(n):
        santa = hat.index(graph[current_column+n+1].index(1)-1)
        giftees[santa] = current_column

        messages[santa] = f"Tu as tiré...|| ** {names[current_column]} ** || !\n"

        if santa_messages and santa_messages[giftees[current_column]]:
            if santa_messages[current_column] != '':
                messages[santa] += f'\nIel t\'a laissé le message suivant: {santa_messages[current_column]}'
            else:
                messages[santa] += "\nIel ne t'a pas laissé de message."

if Config.DRY_RUN:
    for i in range(n):
        print(f'[MESSAGE FOR {names[i]}]')
        print(messages[i])
else:
    if Config.CONTACT_METHOD == 'email':
        client = EmailClient(messages, names, contacts, addresses, giftees)
        client.send_matches()
    elif Config.CONTACT_METHOD == 'discord':
        client = DiscordClient(messages, names, contacts, addresses, giftees)
        client.run()
    else:
        print("You have not selected a valid contact method!\nPlease select either \'email\' or \'discord\' in config.py")
