import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from config import Config

class EmailClient():
    def __init__(self, messages, names, email_addresses, addresses, giftees):
        self.email_addresses = email_addresses
        self.messages = messages
        self.names = names
        self.addresses = addresses
        self.giftees = giftees

    def send_matches(self):
        port = 465  # For SSL
        password = Config.BOT_PASSWORD
        sender_email = Config.BOT_EMAIL

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
            for i in range(len(self.messages)):
                email = MIMEMultipart('alternative')

                email.set_charset('utf8')

                email['FROM'] = sender_email

                # This solved the problem with the encode on the subject.
                email['Subject'] = Header(f"Tirage au sort Secret Santa {self.names[i]}", 'utf-8')
                email['To'] = self.email_addresses[i]

                # And this on the body
                _attach = MIMEText(self.messages[i].encode('utf-8'), 'html', 'UTF-8')

                email.attach(_attach)

                # Create a secure SSL context
                server.sendmail(sender_email, self.email_addresses[i], email.as_string())