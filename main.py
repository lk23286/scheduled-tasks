import os
import requests
from twilio.rest import Client

api_key = os.environ.get("API_KEY")
account_sid = os.environ.get("ACCOUNT_SID")
auth_token = os.environ.get("AUTH_TOKEN")

client = Client(account_sid, auth_token)

OWM_Endpoint = "https://api.openweathermap.org/data/2.5/weather"

weather_params = {
    "lat" : 47.597530,
    "lon" : 19.348030,
    "appid" : api_key
}

response = requests.get(url = OWM_Endpoint, params = weather_params)

data = response.json()
response.raise_for_status()

id = data["weather"][0]["id"]
if id < 900:
    message = client.messages.create(
        messaging_service_sid='MG1a843f9cb83bdcea99c7a35a858705fd',
        body='Github says: Bring Umbrella! ☔️',
        to='+36309843856'
    )

