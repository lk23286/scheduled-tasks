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
    print("API_KEY present:", bool(api_key))
    print("ACCOUNT_SID present:", bool(account_sid))
    print("AUTH_TOKEN present:", bool(auth_token))

    print("ACCOUNT_SID starts with AC:", account_sid.startswith("AC") if account_sid else False)

    client = Client(account_sid, auth_token)

    OWM_Endpoint = "https://api.openweathermap.org/data/2.5/weather"
    id_threshold = 700

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

    if weather_id < id_threshold:
        print("Condition matched, sending SMS...")
        message = client.messages.create(
            messaging_service_sid="MG1a843f9cb83bdcea99c7a35a858705fd",
            body="GitHub happily says: Bring Umbrella! ☔️",
            to="+36309843856"
        )
        print("Twilio SID:", message.sid)
        print("Twilio status:", message.status)
    else:
        print("Condition not matched, no SMS sent.")
        print(f"Weather ID {weather_id} hasn't gone below the threshold {id_threshold}.")



# STOCK:
api_key_for_stock = os.environ.get("API_KEY_FOR_STOCK")
api_key_for_news = os.environ.get("API_KEY_FOR_NEWS")


def stock_main():
    SYMBOL = "TSLA"
    TOPICS = "technology"

    pct_threshold = 0.5

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
    print(stock_data)
    message_stock = f"{SYMBOL} stock has changed  {stock_data["pct_change"]}%"

    news_data = get_news_data_for(topics=TOPICS, stock_data=stock_data)
    #print(news_data)
    message_news = get_best_sentiment_news_for(news_data=news_data)

    pct_change = stock_data.get("pct_change")
    message = f"{message_stock}. Relevant news: {message_news}"
    print(message)

    if pct_threshold < abs(pct_change):
        send_sms(message)
        print("Condition matched, sending Stock SMS...")
    else:
        print(f"Condition not matched, no SMS sent."
              f"The change: {pct_change} hasn't reached the threshold: {pct_threshold}.")


# MAIN
weather_main()
stock_main()
