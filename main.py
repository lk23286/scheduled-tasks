
# COMMON:
import os
import requests
import json
from twilio.rest import Client

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

    if weather_id < 700:
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

#STOCK:
api_key_for_stock = os.environ.get("API_KEY_FOR_STOCK")
api_key_for_news = os.environ.get("API_KEY_FOR_NEWS")
def stock_main():

    SYMBOL = "TSLA"
    TOPICS = "technology"

    pct_thrashold = 10

    def get_stock_data_from_web_for(symbol):
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": api_key_for_stock
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        stock_data_from_web = response.json()
        print(stock_data_from_web)
        series = stock_data_from_web.get("Time Series (Daily)")

        dates = list(series.keys())

        latest_date = dates[0]
        previous_date = dates[1]

        latest_close = float(series[latest_date]['4. close'])
        print(latest_close)

        previous_close = float(series[previous_date]['4. close'])
        print(previous_close)

        return {
            "latest_data": latest_date,
            "previous_data": previous_date,
            "latest_close": latest_close,
            "previous_close": previous_close,
            "change": latest_close - previous_close,
            "pct_change": (100 - latest_close / previous_close * 100),
            "symbol": symbol
        }

    def get_stock_data_for(symbol):
        global is_stock_file_exists
        file_name = "stock"

        try:
            with open(file_name, "r") as f:
                data = json.load(f)
                print("read stock")

        except (FileNotFoundError, json.decoder.JSONDecodeError):
            with open(file_name, "w") as f:
                data = get_stock_data_from_web_for(symbol=symbol)
                json.dump(data, f, indent=4)
                print("write stock")
        return data

    def get_news_from_web(symbol, topics, previous_data, latest_data):
        time_from = previous_data.replace("-", "") + "T0000"
        time_to = latest_data.replace("-", "") + "T2359"
        print(f"time_from: {time_from}")
        print(f"time_to: {time_to}")

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

        return news_data

    def get_news_for(stock_data, topics):
        file_name = "news"
        news_data = {}

        try:
            with open(file_name, "r") as f:
                news_data = json.load(f)
                print("read news")

        except (FileNotFoundError, json.decoder.JSONDecodeError):

            previous_date = stock_data["previous_data"]
            latest_date = stock_data["latest_data"]
            symbol = stock_data["symbol"]
            print(f"previous_date: {previous_date}")
            print(f"latest_date: {latest_date}")
            print(f"symbol: {symbol}")
            news_data = get_news_from_web(symbol=symbol, topics=topics, previous_data=previous_date,
                                          latest_data=latest_date)

            with open(file_name, "w") as f:
                json.dump(news_data, f, indent=4)
                print("write news")

        return news_data.get("feed", [])

    def find_max_sentiment_news_in(news_data, symbol):

        max_score = 0
        news_count = 0

        news_sentiment_score = 0
        news_label = ""
        max_count = 0

        for news in news_data:

            ticker_sentiments = news["ticker_sentiment"]

            for ticker_sentiment in ticker_sentiments:

                ticker = ticker_sentiment["ticker"]

                if ticker == symbol:
                    ticker_sentiment_score = abs(float(ticker_sentiment["ticker_sentiment_score"]))

                    if max_score < ticker_sentiment_score:
                        max_score = ticker_sentiment_score
                        max_count = news_count

                        news_label = ticker_sentiment["ticker_sentiment_label"]
                        news_sentiment_score = round(float(ticker_sentiment["ticker_sentiment_score"]), 2)

            news_count += 1

        news_title = news_data[max_count]['title']
        news_url = news_data[max_count]['url']

        return f"{news_sentiment_score}, {news_label}, {news_title}, {news_url}"

    def send_sms(message):
        to_phone_number = "+36309843856"

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            messaging_service_sid='MG1a843f9cb83bdcea99c7a35a858705fd',
            body=message,
            to=to_phone_number
        )

    def remove_files():
        for filename in ["news", "stock"]:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"file removed: {filename}")
            else:
                print(f"file not removed: {filename}")

    stock_data = get_stock_data_for(symbol=SYMBOL)
    print(stock_data)

    news_data = get_news_for(stock_data, TOPICS)

    message = find_max_sentiment_news_in(news_data, SYMBOL)
    print(message)

    pct_change = round(stock_data.get("pct_change"), 2)
    print(f"pct_change: {pct_change}")

    if pct_thrashold < pct_change:
        send_sms(message)
        print("Message was sent")
    else:
        print(f"Message was not sent,"
              f" change: {pct_change} hasn't reached the threshold: {pct_thrashold}")

    # unmark the below remove_files() if you would like to create fresh daily data from the stock
        # if you don't unmark it than only one time will be created fresh data and
        # after that the data from the files will be used
    #remove_files()

#MAIN
weather_main()
stock_main()

