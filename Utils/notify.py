import os
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


# def set_env_from_file(file_name):
#     lines = open(file_name).readlines()
#     export_lines = [l[7:].replace('\n', '') for l in lines if l.startswith('export')]
#     vars = {x.split('=')[0]: x.split('=')[1] for x in export_lines}
#     for k, v in vars.items():
#         os.environ[k] = v


class SMSNotify:
    def __init__(self):
        # print('Reading cred from env')
        # set_env_from_file('sms_env.sh')
        TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
        TWILIO_ACCOUNT_TOKEN = os.environ.get('TWILIO_ACCOUNT_TOKEN')
        TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
        TWILIO_TO_NUMBER = os.environ.get('TWILIO_TO_NUMBER')

        creds = dict(TWILIO_ACCOUNT_SID=TWILIO_ACCOUNT_SID, TWILIO_ACCOUNT_TOKEN=TWILIO_ACCOUNT_TOKEN,
                     TWILIO_FROM_NUMBER=TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER=TWILIO_TO_NUMBER)

        self.creds = creds
        self.client = Client(creds['TWILIO_ACCOUNT_SID'], creds['TWILIO_ACCOUNT_TOKEN'])

    def send(self, txt):
        try:
            message = self.client.messages.create(
                to=self.creds['TWILIO_TO_NUMBER'],
                from_=self.creds['TWILIO_FROM_NUMBER'],
                body=txt)
            print(message.sid)
        except TwilioRestException:
            print('Something is wrong with sms sending')


class TelegramBot:
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_TOKEN')
        self.group_id = os.environ.get('TELEGRAM_GROUP')
        if self.bot_token is None or self.group_id is None:
            raise ValueError('token or group id not set')
        # self.bot_user_name = "oracle23_bot"
        self.url = "https://api.telegram.org/bot{token}/sendMessage?chat_id={group_id}&text={msg}&parse_mode=HTML"

    def send(self, txt):
        url = self.url.format(token=self.bot_token, group_id=self.group_id, msg=txt)
        try:
            resp = requests.get(url)
            print(resp.text)
        except requests.ConnectionError as e:
            print('Something is wrong with telegram api')
            print(e)
