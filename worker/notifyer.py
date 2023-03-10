import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app import app
from worker.Config import Config

config = Config().get_config()


class NotificationFactory:
    """
    Factory for notification methods. Simple to extend for new methods.
    """

    @staticmethod
    def create_notification(notification_type, recipient, message):
        if notification_type == 'email':
            return EmailNotification(recipient, message)
        elif notification_type == 'sms':
            pass
            # return SMSNotification(recipient, sender)
        else:
            raise ValueError('Invalid notification type')


class EmailNotification(NotificationFactory):
    host = config["SMTP_SERVER"]
    port = config["SMTP_PORT"]
    login = config["SMTP_LOGIN"]
    password = config["SMTP_PASSWORD"]

    def __init__(self, recipient, message):
        self.recipient = recipient
        self.message = message

    def send_notification(self):
        app.logger.info(f'Creating notification for {self.recipient}')
        s = smtplib.SMTP(host=self.host, port=int(self.port))
        s.starttls()
        s.login(self.login, self.password)

        msg = MIMEMultipart()  # create a message

        # setup the parameters of the message
        msg['From'] = self.login

        msg['To'] = self.recipient
        msg['Subject'] = "Alert from RSS Scraper Notifier"

        # add in the message body
        msg.attach(MIMEText(self.message, 'plain'))

        # send the message via the server set up earlier.
        s.send_message(msg)
        app.logger.info(f'Notification with text {msg} sent to {self.recipient}')
        del msg

        # Terminate the SMTP session and close the connection
        s.quit()
