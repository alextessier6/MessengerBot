import requests
import datetime
import Config  # File used to store API keys
from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask, request
from pymessenger.bot import Bot


scheduler = BackgroundScheduler()

app = Flask(__name__)
ACCESS_TOKEN = Config.ACCESS_TOKEN
VERIFY_TOKEN = Config.VERIFY_TOKEN
caspian = Bot(ACCESS_TOKEN)
recipient_id = Config.recipient_id  # Set to only 1 user


@app.route('/', methods=['GET', 'POST'])
def receive_message():

    # Used by Facebook to confirm requests
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)

    # Received message from user
    else:
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message'):
                    if message['message'].get('text'):
                        if "weather" in message['message']['text'].lower():
                            send_weather()
                        else:
                            send_message(recipient_id, "Waddup bitch")

        return "Message Processed"


# Verifies if token sent by facebook matches the verify token
def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

def send_message(recipient_id, response):
    caspian.send_text_message(recipient_id, response)
    return "success"


def send_greetings():
    # Server time is in UTC time zone (UTC = EST + 5)
    timestamp = datetime.datetime.now().time()
    morning_start = datetime.time(5) # 0 AM EST
    morning_end = datetime.time(17) # 12PM EST
    afternoon_end = datetime.time(23) # 6PM EST
    evening_end = datetime.time(4, 59) # 23:59 EST

    if morning_start <= timestamp <= morning_end:
        message = "Good morning!"
    if morning_end <= timestamp <= afternoon_end:
        message = "Good afternoon!"
    if afternoon_end <= timestamp or timestamp <= evening_end:
        message = "Good evening!"
    send_message(recipient_id, message)
    return "success"


def send_weather():
    r = requests.get(Config.weather_link)
    j = r.json()

    high = j["forecast"]["simpleforecast"]["forecastday"][0]["high"]["celsius"]
    low = j["forecast"]["simpleforecast"]["forecastday"][0]["low"]["celsius"]
    condition = j["forecast"]["simpleforecast"]["forecastday"][0]["conditions"]
    precipitations_mm = j["forecast"]["simpleforecast"]["forecastday"][0]["qpf_day"]["mm"]
    snow_cm = j["forecast"]["simpleforecast"]["forecastday"][0]["snow_day"]["cm"]

    # Could eventually implement call to Hourly API to tell at what time it should start to rain
    message = ""
    if precipitations_mm != 0 and precipitations_mm is not None:
        message = "Rain is in the forecast! About " + str(precipitations_mm) + "mm of rain is expected. "
    if snow_cm != 0 and snow_cm is not None:
        message = "Snow is in the forecast! About " + str(snow_cm) + "cm of snow is expected. "
    message += "The condition for today is \"" + condition + "\" with a high of " + high + " and a low of " + low + "."
    send_greetings()
    send_message(recipient_id, message)


if __name__ == '__main__':
    app.run()
    scheduler.start()
    scheduler.add_job(send_weather, 'cron', hour='11', minute='15') # 6:15 EST