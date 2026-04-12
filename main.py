# Created: 2026.04.12 by LGL
#
# Schedule the Weather and Stock application to run daily at 07:30
# and send an SMS to the phone number +36 30 984 3856
# if any of the following conditions are met:
#
#   - Weather condition exceeds id_threshold
#   - Stock condition exceeds pct_threshold
#
# Thresholds can be adjusted inside the configuration of the apps



# COMMON:
import os
import requests
from twilio.rest import Client
import sys

# WEATHER:
api_key = os.environ.get("API_KEY")
account_sid = os.environ.get("ACCOUNT_SID")
auth_token = os.environ.get("AUTH_TOKEN")


def weather_main():
    sms_message = "Bring Umbrella! ☔️"
    OWM_Endpoint = "https://api.openweathermap.org/data/2.5/weather"

    # This data defines when the SMS is sent out.
    # weather["id"] = numeric weather condition code.
    # It’s a code grouped by weather category:
    # Range	Meaning
    # 200–232	Thunderstorm ⛈️
    # 300–321	Drizzle 🌦️
    # 500–531	Rain 🌧️
    # 600–622	Snow ❄️
    # 700–781	Atmosphere (fog, dust) 🌫️
    # 800	Clear ☀️
    # 801–804	Clouds ☁️
    # The value under 700 is rainy weather
    id_threshold = 900

    weather_params = {
        "lat": 47.597530,
        "lon": 19.348030,
        "appid": api_key
    }

    client = Client(account_sid, auth_token)

    print("Weather app:")
    response = requests.get(url=OWM_Endpoint, params=weather_params, timeout=30)
    response.raise_for_status()

    data = response.json()
    weather_id = data["weather"][0]["id"]

    if weather_id < id_threshold:
        print("Weather condition matched, sending SMS...")
        print(f"Weather ID {weather_id} has gone below the threshold {id_threshold}.")
        print(f"SMS message: {sms_message}")

        message = client.messages.create(
            messaging_service_sid="MG1a843f9cb83bdcea99c7a35a858705fd",
            body=sms_message,
            to="+36309843856"
        )

    else:
        print("Weather condition not matched, no SMS sent.")
        print(f"Weather ID {weather_id} hasn't gone below the threshold {id_threshold}.")

    print("")

# STOCK:
api_key_for_stock = os.environ.get("API_KEY_FOR_STOCK")
api_key_for_news = os.environ.get("API_KEY_FOR_NEWS")


def stock_main():
    # The Symbol defines the stock that you would like to check
    SYMBOL = "TSLA"
    # The 'topics' parameter defines which news categories will be monitored.
    TOPICS = "technology"

    # This data defines when the SMS is sent out.
    # It is the precentage of the stock value changing between the latest two subsequent day's at the closing time.
    pct_threshold = 0.5 # percentage %

    print("Stock app:")

    def get_stock_data_for(symbol):
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": api_key_for_stock
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        stock_data_from_web = response.json()

        if "Information" in stock_data_from_web:
            print(stock_data_from_web["Information"])
            print("You have reached the rate limit for this day. Script can run tomorrow.")
            sys.exit()

        series = stock_data_from_web.get("Time Series (Daily)")

        dates = list(series.keys())

        latest_date = dates[0]
        previous_date = dates[1]
        latest_close = float(series[latest_date]['4. close'])
        previous_close = float(series[previous_date]['4. close'])

        return {
            "latest_data": latest_date,
            "previous_data": previous_date,
            "latest_close": latest_close,
            "previous_close": previous_close,
            "change": latest_close - previous_close,
            "pct_change": round((100 - latest_close / previous_close * 100),2),
            "symbol": symbol
        }

    def get_news_data_for(topics, stock_data):
        previous_data = stock_data["latest_data"]
        latest_data = stock_data["latest_data"]
        symbol = stock_data["symbol"]

        time_from = previous_data.replace("-", "") + "T0000"
        time_to = latest_data.replace("-", "") + "T2359"

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "time_from": time_from,  # format: YYYYMMDDTHHMM
            "time_to": time_to,
            "topics": topics,
            "sort": "RELEVANCE",
            "limit": 5,
            "apikey": api_key_for_news
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        news_data = response.json()

        return news_data.get("feed", []), symbol

    def get_best_sentiment_news_for(news_data):

        feeds, symbol = news_data


        max_score = 0
        count = 0

        news_sentiment_score = 0
        news_label = ""
        max_count = 0

        for feed in feeds:

            ticker_sentiments = feed["ticker_sentiment"]

            for ticker_sentiment in ticker_sentiments:

                ticker = ticker_sentiment["ticker"]

                if ticker == symbol:
                    ticker_sentiment_score = abs(float(ticker_sentiment["ticker_sentiment_score"]))

                    if max_score < ticker_sentiment_score:
                        max_score = ticker_sentiment_score
                        max_count = count

                        news_label = ticker_sentiment["ticker_sentiment_label"]
                        news_sentiment_score = round(float(ticker_sentiment["ticker_sentiment_score"]), 2)

            count += 1

        news_title = feeds[max_count]['title']
        news_url = feeds[max_count]['url']

        return f"{news_sentiment_score}, {news_label}, {news_title}, {news_url}"

    def send_sms(message):
        to_phone_number = "+36309843856"

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            messaging_service_sid='MG1a843f9cb83bdcea99c7a35a858705fd',
            body=message,
            to=to_phone_number
        )


    stock_data = get_stock_data_for(symbol=SYMBOL)
    message_stock = f"{SYMBOL} stock has changed  {stock_data["pct_change"]}%"

    news_data = get_news_data_for(topics=TOPICS, stock_data=stock_data)
    message_news = get_best_sentiment_news_for(news_data=news_data)

    pct_change = abs(stock_data.get("pct_change"))
    message = f"{message_stock}. Relevant news: {message_news}"

    if pct_threshold < pct_change:
        send_sms(message)
        print("Stock condition matched, sending SMS...")
        print(f"The change: {pct_change} has reached the threshold: {pct_threshold}.")
        print(f"SMS message: {message}")
    else:
        print(f"Stock condition not matched, no SMS sent.")
        print(f"The change: {pct_change} hasn't reached the threshold: {pct_threshold}.")

    print("")

# MAIN
weather_main()
stock_main()
