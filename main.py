from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import discord
import random
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

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

            bodyStr = ''
            #This solved the problem with the encode on the subject.
            email['Subject'] = Header(f"Tirage au sort Secret Santa {names[i]}",'utf-8')
            email['To'] = contacts[i]

            # And this on the body
            _attach = MIMEText(messages[i].encode('utf-8'), 'html', 'UTF-8')        

            email.attach(_attach)

            # Create a secure SSL context
            server.sendmail(sender_email, contacts[i], email.as_string())

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

i += 1
contacts = [line[i] for line in  result_input.get('values', [])]

if Config.HAS_ADDRESS:
    i += 1
    addresses = [line[i] for line in result_input.get('values', [])]

i += 1
secretMessages = [line[i] for line in  result_input.get('values', [])]


if Config.HAS_CONFLICT_MANAGEMENT:
    i += 1

conflicts = [[names.index(name) for name in (line[i].split(',') if Config.HAS_CONFLICT_MANAGEMENT and len(line) > i else [])] for line in result_input.get('values', [])]

for c in range(n):
    conflicts[c] += [c]
    
print(conflicts)


print("This script will send a message to the " + str(n) + " following people:")
for contact in contacts:
    print(contact)

if Config.DRY_RUN:
    print('[THIS IS A DRY RUN]')

if input("Do you want to proceed?(yes/no)") != "yes":
    print("Aborting...")
    sys.exit()

graph = [[0]*(2*n+2) for _ in range(2*n+2)] 
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
        santa = hat.index(graph[i+n+1].index(1)-1)
        giftees[santa] = i

        message[santa] = f'Your giftee is ||{names[i]}|| !\n'
        
        if Config.HAS_ADDRESS:
            message[santa] = f'Their address is:\n||{addresses[i]}||\n'
        
        if secretMessages[giftees[i]]:
            message[santa] += f'They left the following message for you: \n||{secretMessages[i]}||\n'
        

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    #for m in client.get_all_members():
    #    print(m)
    fail = False
    successful_users = []
    for i in range(n):
        user = discord.utils.get(client.get_all_members(), name=contacts[i][:-5], discriminator=contacts[i][-4:])
        if user is None:
            print("user " + contacts[i] + " not found", file=sys.stderr)
            fail = True
        else:
            try:
                await user.send("Matching is about to begin, please wait")
            except:
                print("Could not DM user " + contacts[i])
                fail = True
            else:
                successful_users+=[user]
    if fail:
        print("Aborting...")
        for u in successful_users:
            await u.send("Une erreur est survenue lors du tirage au sort, et il a été abandonné.")

    else:
        for i in range(len(successful_users)):
            await successful_users[i].send(message[i])
        print("Done!")
    await client.close()

if Config.DRY_RUN:
    for i in range(n):
        print(f'[MESSAGE FOR {names[i]}]')
        print(message[i])
else:
    if Config.CONTACT_METHOD == 'email':
        send_emails(message, names)
        print("Done!")
    elif Config.CONTACT_METHOD == 'discord':
        client.run(Config.DISCORD_BOT_TOKEN)
        print("Done!")
    else:
        print("You have not selected a valid contact method!\nPlease select either \'email\' or \'discord\' in config.py")
