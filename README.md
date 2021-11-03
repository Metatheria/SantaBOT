**Secret Santa Bot**

This bot matches people for a Secret Santa by taking their infos from a Google Sheet (which you can create through a form) and DMing them automatically on Discord.

**Sheet format**

Column B (starting at B2) should contain participants' usernames and discriminants (xyzxyz#1234)

Column C (starting at C2) should contain their address

Column D (starting at D2) should contain an (optional) message from giftees to their Santa

**How to use it?**

1-Install dependencies ``pip install -r requirements.txt``.

2-Create a project on [Google Cloud](https://console.cloud.google.com/home/dashboard).

3-Go to "API and Services", then browse the library and add the Google Sheet API.

4-Add a service account, and generate a json key for that account. Put that json in the same file as the script.

5-Copy the sheet's id into the code (the link should look like docs.google.com/spreadsheets/d/**xxxxxxxxxxxxxxxxxxxxxxxxxxxx**/edit[...], just copy the part in bold). Make sure you give at least read access to people with the link to your sheet.

6-Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.

7-Copy the bot's token into the code.

8-Invite the bot to a server with all the participants.

9-Run the bot with ``python main.py``
