import os
import requests
from twilio.rest import Client

api_key = os.environ.get("API_KEY")
account_sid = os.environ.get("ACCOUNT_SID")
auth_token = os.environ.get("AUTH_TOKEN")

print("API_KEY present:", bool(api_key))
print("ACCOUNT_SID present:", bool(account_sid))
print("AUTH_TOKEN present:", bool(auth_token))

client = Client(account_sid, auth_token)

OWM_Endpoint = "https://api.openweathermap.org/data/2.5/weather"

weather_params = {
    "lat": 47.597530,
    "lon": 19.348030,
    "appid": api_key
}

response = requests.get(url=OWM_Endpoint, params=weather_params, timeout=30)
print("Weather status:", response.status_code)
response.raise_for_status()

data = response.json()
weather_id = data["weather"][0]["id"]
print("Weather ID:", weather_id)
print("Weather main:", data["weather"][0]["main"])
print("Weather description:", data["weather"][0]["description"])

if weather_id < 900:
    print("Condition matched, sending SMS...")
    message = client.messages.create(
        messaging_service_sid="MG1a843f9cb83bdcea99c7a35a858705fd",
        body="GitHub says: Bring Umbrella! ☔️",
        to="+36309843856"
    )
    print("Twilio SID:", message.sid)
    print("Twilio status:", message.status)
else:
    print("Condition not matched, no SMS sent.")
