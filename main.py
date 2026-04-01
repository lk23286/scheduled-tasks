import os
import requests
from twilio.rest import Client

api_key = os.environ.get("API_KEY")
account_sid = os.environ.get("ACCOUNT_SID")
auth_token = os.environ.get("AUTH_TOKEN")


# print(f"auth_token: {auth_token}")
# print(f"api_key: {api_key}")
# print(f"account_sid: {account_sid}")
client = Client(account_sid, auth_token)



OWM_Endpoint = "https://api.openweathermap.org/data/2.5/weather"



weather_params = {
    "lat" : 47.597530,
    "lon" : 19.348030,
    "appid" : api_key
}

response = requests.get(url = OWM_Endpoint, params = weather_params)
#print(response.status_code)
data = response.json()
response.raise_for_status()
#print(data)
#print(json.dumps(data, indent=4))
id = data["weather"][0]["id"]
if id < 900:
    #print("Bring Umbrella")
    message = client.messages.create(
        messaging_service_sid='MG1a843f9cb83bdcea99c7a35a858705fd',
        body='Bring Umbrella! ☔️',
        to='+36309843856'
    )
    #print(message.sid)

#print(f"id:{id}")
