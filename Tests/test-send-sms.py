import os


def test_env(env_name, env_key):
    got_key = os.environ.get(env_name)
    print(got_key)
    assert got_key == env_key


def send_sms(creds, body_txt):
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException

    client = Client(creds['TWILIO_ACCOUNT_SID'], creds['TWILIO_ACCOUNT_TOKEN'])
    try:
        message = client.messages.create(
            to=creds['TWILIO_TO_NUMBER'],
            from_=creds['TWILIO_FROM_NUMBER'],
            body=body_txt)
        print(message.sid)
    except TwilioRestException:
        print('Something is wrong with sms sending')


def set_env_from_file(file_name):
    lines = open(file_name).readlines()
    export_lines = [l[7:].replace('\n', '') for l in lines if l.startswith('export')]
    vars = {x.split('=')[0]: x.split('=')[1] for x in export_lines}
    for k, v in vars.items():
        os.environ[k] = v


if __name__ == '__main__':
    # os.system('bash sms_env.sh')
    set_env_from_file('sms_env.sh')

    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_ACCOUNT_TOKEN = os.environ.get('TWILIO_ACCOUNT_TOKEN')
    TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
    TWILIO_TO_NUMBER = os.environ.get('TWILIO_TO_NUMBER')

    creds = dict(TWILIO_ACCOUNT_SID=TWILIO_ACCOUNT_SID, TWILIO_ACCOUNT_TOKEN=TWILIO_ACCOUNT_TOKEN,
                 TWILIO_FROM_NUMBER=TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER=TWILIO_TO_NUMBER)

    import datetime

    txt_body = "    היי! זו דני    " + str(datetime.datetime.now())

    send_sms(creds, txt_body)
