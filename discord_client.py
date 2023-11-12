import discord
import sys


def split(message):
    start_index = 0
    parts = []
    while len(message[start_index:]) > 2000:
        final_index = min(start_index+1999, len(message)-1)
        while message[final_index] != ' ':
            final_index -= 1
            if final_index == start_index:#if there are no spaces to split around
                final_index = start_index+1999
                break
        parts.push(message[start_index:final_index])
        start_index = final_index+2
    parts.append(message[start_index:])
    return parts


class DiscordClient(discord.Client):
    def __init__(self, messages, names, usernames, addresses, giftees):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)

        self.usernames = usernames
        self.messages = messages
        self.names = names
        self.addresses = addresses
        self.giftees = giftees

    async def on_ready(self):
        print(f"We have logged in as {self.user}")
        await self.send_matches()

    async def send_matches(self):
        fail = False
        successful_users = []

        for i in range(len(self.messages)):
            user = discord.utils.get(self.get_all_members(),
                                    name=self.usernames[i])
            if user is None:
                print("user " + self.usernames[i] + " not found",
                    file=sys.stderr)

                fail = True
            else:
                try:
                    await user.send("Le tirage au sort va commencer, veuillez patienter...")
                except:

                    print("Could not DM user " + self.usernames[i])

                    fail = True
                else:
                    successful_users += [user]
        if fail:
            print("Aborting...")

            for user in successful_users:
                await user.send("Une erreur est survenue lors du tirage au sort, et il a été abandonné.")
                raise RuntimeError

        else:
            for i in range(len(successful_users)):
                for part in split(self.messages[i]):
                    await successful_users[i].send(part)
    
    async def send_message(self, username, message):
        await self.wait_until_ready()
        user = discord.utils.get(self.get_all_members(),
                                    name=username)
        try:
            await user.send(message)
        except:
            print("Could not DM user " + username)
