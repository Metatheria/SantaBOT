"""Module launching the whole Secret Santa workflow"""

import random
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from googleapiclient.discovery import build
from google.oauth2 import service_account
import discord

from config import Config
from maxflow import maxflow


def send_emails(messages, names):
    port = 465  # For SSL
    password = Config.BOT_PASSWORD
    sender_email = Config.BOT_EMAIL

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, password)
        for i in range(n):
            email = MIMEMultipart('alternative')

            email.set_charset('utf8')

            email['FROM'] = sender_email

            # This solved the problem with the encode on the subject.
            email['Subject'] = Header(f"Tirage au sort Secret Santa {names[i]}", 'utf-8')
            email['To'] = contacts[i]

            # And this on the body
            _attach = MIMEText(messages[i].encode('utf-8'), 'html', 'UTF-8')

            email.attach(_attach)

            # Create a secure SSL context
            server.sendmail(sender_email, contacts[i], email.as_string())

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

creds = service_account.Credentials.from_service_account_file(
        Config.GOOGLE_KEY_FILE,
        scopes=Config.SHEETS_SCOPES)

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result_input = sheet.values().get(spreadsheetId=Config.SPREADSHEET_ID,
                                  range=Config.RANGE_NAME).execute()

# print(result_input.get('values', []))

current_column = 0
names = [line[current_column] for line in result_input.get('values', [])]

if not names:
    print('No data found.')
    sys.exit(1)

n = len(names)

current_column += 1
contacts = [line[current_column]
            for line in result_input.get('values', [])]

if Config.HAS_ADDRESS:
    current_column += 1
    addresses = [line[current_column]
                 for line in result_input.get('values', [])]

current_column += 1
secretMessages = [(line[current_column] if len(line) > current_column else '')
                  for line in result_input.get('values', [])]

if Config.HAS_CONFLICT_MANAGEMENT:
    current_column += 1

conflicts = [[names.index(name)
              for name in (line[current_column].split(',')
                           if Config.HAS_CONFLICT_MANAGEMENT
                           and len(line) > current_column else [])]
             for line in result_input.get('values', [])]

for c in range(n):
    conflicts[c] += [c]

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

        messages[santa] = f"Ton bébé Noël est...|| ** {names[current_column]} ** || !\n"

        if Config.HAS_ADDRESS:
            messages[santa] += f'\nSon adresse est:\n {addresses[current_column]} \n'

        if secretMessages[giftees[current_column]]:
            if secretMessages[current_column] != '':
                messages[santa] += f'\nIel t\'a laissé le message suivant: {secretMessages[current_column]}'
            else:
                messages[santa] += "\nIel ne t'a pas laissé de message."


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # for m in client.get_all_members():
    #     print(m)
    fail = False
    successful_users = []

    for i in range(n):
        user = discord.utils.get(client.get_all_members(),
                                 name=contacts[i][:-5],
                                 discriminator=contacts[i][-4:])
        if user is None:
            print("user " + contacts[i] + " not found",
                  file=sys.stderr)

            fail = True
        else:
            try:
                await user.send("Le tirage au sort va commencer, veuillez patienter...")
            except:

                print("Could not DM user " + contacts[i])

                fail = True
            else:
                successful_users += [user]
    if fail:
        print("Aborting...")

        for user in successful_users:
            await user.send("Une erreur est survenue lors du tirage au sort, et il a été abandonné.")

    else:
        for i in range(len(successful_users)):
            start_index = 0
            while len(messages[i][start_index:]) > 2000:
                final_index = min(start_index+1999, len(messages[i])-1)
                while messages[i][final_index] != ' ':
                    final_index -= 1

                await successful_users[i].send(
                        messages[i][start_index:final_index])
                start_index = final_index+2
            await successful_users[i].send(
                    messages[i][start_index:])

    await client.close()

if Config.DRY_RUN:
    for i in range(n):
        print(f'[MESSAGE FOR {names[i]}]')
        print(messages[i])
else:
    if Config.CONTACT_METHOD == 'email':
        send_emails(messages, names)
        print("Done!")
    elif Config.CONTACT_METHOD == 'discord':
        client.run(Config.DISCORD_BOT_TOKEN)
        print("Done!")
    else:
        print("You have not selected a valid contact method!\nPlease select either \'email\' or \'discord\' in config.py")
