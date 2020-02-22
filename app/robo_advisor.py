import csv
import json
import os

from datetime import datetime, timedelta

from dotenv import load_dotenv
import requests

load_dotenv()

import matplotlib.pyplot as plt
import pandas as pd

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# utility function to convert float or integer to usd-formatted string (for printing)
# ... adapted from: https://github.com/s2t2/shopping-cart-screencast/blob/30c2a2873a796b8766
def to_usd(my_price):
    return "${0:,.2f}".format(my_price)

#
# INFO INPUTS
#

api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
symbol = input("Please choose a valid stock symbol to evaluate: ") #accept user input
length = len(symbol)
request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"

if symbol.isdigit() or (length < 1 or length > 5): # source: https://pynative.com/python-check-user-input-is-number-or-string/
    print("Oh, expecting a properly-formed stock symbol like 'MSFT'. The program will now exit, so please try again.")
    exit()
else:
    response = requests.get(request_url)
    # print(type(response)) # <class 'requests.models.Response'>
    # print(response.status_code) # 200 
    # print(response.text)

    # handle response errors:
    if "Error Message" in response.text:
        print("Oops, couldn't find that symbol. The program will now exit, so please try again.")
        exit()

    parsed_response = json.loads(response.text)

    last_refreshed = parsed_response["Meta Data"]["3. Last Refreshed"]

    tsd = parsed_response["Time Series (Daily)"]
    dates = list(tsd.keys())
    latest_day = dates[0]
    latest_close = parsed_response["Time Series (Daily)"][latest_day]["4. close"]

    # maximum of all high prices
    high_prices = []
    low_prices = []

    for date in dates:
        high_price = tsd[date]["2. high"]
        low_price = tsd[date]["3. low"]
        high_prices.append(float(high_price))
        low_prices.append(float(low_price))

    recent_high = max(high_prices)
    recent_low = min(low_prices)

    # sending alerts via email 
    current_datetime = datetime.now() # source: tecadmin.net/get-current-date-time-python/

    while True:
        email_choice = input("Would you like to receive an email alerting you about price movements? (Yes or No): ")

        second_latest_close = parsed_response["Time Series (Daily)"][dates[1]]["4. close"]
        second_latest_day = list(tsd.keys())[1]
        timestamp = current_datetime.strftime("%B %d, %Y at %I:%M %p")

        if email_choice.lower() == "yes":
            print("Great! You'll receive an email if there was a price movement within the past day of the latest day's stock.")

            if (float(latest_close) < .95*(float(second_latest_close))):
                SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "OOPS, please set env var called 'SENDGRID_API_KEY'")
                MY_ADDRESS = os.environ.get("MY_EMAIL_ADDRESS", "OOPS, please set env var called 'MY_EMAIL_ADDRESS'")

                client = SendGridAPIClient(SENDGRID_API_KEY) #> <class 'sendgrid.sendgrid.SendGridAPIClient>
                print("CLIENT:", type(client))

                subject = f"PRICE MOVEMENT ALERT FOR {symbol}!"

                # body of the email
                html_content = f"""
                    <h3>PRICE DECREASE FOR {symbol}!</h3>
                    <p>Date: {timestamp}</p>
                    <p>The price has decreased by more than 5% within the past day of the latest day's stock. The closing price for {second_latest_day} was {second_latest_close}, decreasing to {latest_close} for {last_refreshed}.
                    <h3>Thank you for using Robo Advisor.</h3>
                """

                print("HTML:", html_content)

                message = Mail(from_email=MY_ADDRESS, to_emails=MY_ADDRESS, subject=subject, html_content=html_content)

                try:
                    response = client.send(message)

                    print("RESPONSE:", type(response)) #> <class 'python_http_client.client.Response'>
                    print(response.status_code) #> 202 indicates SUCCESS
                    print(response.body)
                    print(response.headers)

                except Exception as e:
                    print("OOPS", e.message)
                
                break
            elif (float(latest_close) > 1.05*(float(second_latest_close))):
                SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "OOPS, please set env var called 'SENDGRID_API_KEY'")
                MY_ADDRESS = os.environ.get("MY_EMAIL_ADDRESS", "OOPS, please set env var called 'MY_EMAIL_ADDRESS'")

                client = SendGridAPIClient(SENDGRID_API_KEY) #> <class 'sendgrid.sendgrid.SendGridAPIClient>
                print("CLIENT:", type(client))

                subject = f"PRICE MOVEMENT ALERT FOR {symbol}!"

                # body of the email
                html_content = f"""
                    <h3>PRICE INCREASE FOR {symbol}!</h3>
                    <p>Date: {timestamp}</p>
                    <p>The price has increased by more than 5% within the past day of the latest day's stock. The closing price for {second_latest_day} was {second_latest_close}, increasing to {latest_close} for {last_refreshed}.
                    <h3>Thank you for using Robo Advisor.</h3>
                """

                print("HTML:", html_content)

                message = Mail(from_email=MY_ADDRESS, to_emails=MY_ADDRESS, subject=subject, html_content=html_content)

                try:
                    response = client.send(message)

                    print("RESPONSE:", type(response)) #> <class 'python_http_client.client.Response'>
                    print(response.status_code) #> 202 indicates SUCCESS
                    print(response.body)
                    print(response.headers)

                except Exception as e:
                    print("OOPS", e.message)
                
                break
            else:
                break
        elif email_choice.lower() == "no":
            break
        else:
            print("Sorry, that isn't a valid choice. Please choose 'Yes' or 'No'.")

    #
    # INFO OUTPUTS
    #

    # csv_file_path = "data/prices.csv"
    ## creating a csv file of the stock prices
    csv_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "prices.csv")

    csv_headers = ["timestamp", "opening", "high", "low", "closing", "volume"]
    with open(csv_file_path, "w", newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
        writer.writeheader()

        # looping
        for date in dates:
            daily_prices = tsd[date]
            writer.writerow({
                "timestamp": date,
                "opening": daily_prices["1. open"],
                "high": daily_prices["2. high"],
                "low": daily_prices["3. low"],
                "closing": daily_prices["4. close"],
                "volume": daily_prices["5. volume"]
            })

    print("-------------------------")
    print("SELECTED SYMBOL: " + symbol)
    print("-------------------------")
    print("REQUESTING STOCK MARKET DATA...")

    ## print current date and time
    print("REQUEST AT: " + current_datetime.strftime("%Y-%m-%d %I:%M %p"))
    print("-------------------------")
    print(f"LATEST DAY: {last_refreshed}")
    print(f"LATEST CLOSE: {to_usd(float(latest_close))}")
    print(f"RECENT HIGH: {to_usd(float(recent_high))}")
    print(f"RECENT LOW: {to_usd(float(recent_low))}")
    print("-------------------------")
    
    ## recommendation algorithm
    if (float(latest_close) >= recent_low) and (float(latest_close) < 1.2*recent_low):
        print("RECOMMENDATION: BUY!")
        print("RECOMMENDATION REASON: BECAUSE THE STOCK'S LATEST CLOSE IS LESS THAN 20% ABOVE ITS RECENT LOW")
    else:
        print("RECOMMENDATION: DON'T BUY")
        print("RECOMMENDATION REASON: BECAUSE THE STOCK'S LATEST CLOSE IS BEYOND 20% ABOVE THE RECENT LOW")
    print("-------------------------")
    print(f"WRITING DATA TO CSV: {csv_file_path}...")
    print("-------------------------")
    print("GENERATING LINE GRAPHS...")
    print("-------------------------")
    print("HAPPY INVESTING!")
    print("-------------------------")


    # creating four line graphs showing the opening, high, low, and closing stock prices over time
    ## source: https://stackoverflow.com/questions/56179109/plot-stock-data-from-csv-file-not-showing-date-correctly
    stock_prices = pd.read_csv('data/prices.csv')

    ## Convert the date to datetime
    stock_prices['timestamp'] = pd.to_datetime(stock_prices['timestamp'], format = '%Y-%m-%d')
    ## Assign this as index
    stock_prices.set_index(['timestamp'], inplace=True)
    ## plot the price -- making subplots source: https://pythonprogramming.net/matplotlib-tutorial-part-5-subplots-multiple-plots-figure/
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, sharex=True, sharey=True)

    ax1.plot(stock_prices['opening'], 'r')
    ax2.plot(stock_prices['high'], 'b')
    ax3.plot(stock_prices['low'], 'g')
    ax4.plot(stock_prices['closing'], 'k')

    ## setting subplot labels
    ax1.set_title(f'Opening Stock Prices Over Time for {symbol}')
    ax2.set_title(f'High Stock Prices Over Time for {symbol}')
    ax3.set_title(f'Low Stock Prices Over Time for {symbol}')
    ax4.set_title(f'Closing Stock Prices Over Time for {symbol}')

    ax3.set_xlabel('Day')
    ax4.set_xlabel('Day')
    ax1.set_ylabel('Price')
    ax3.set_ylabel('Price')

    plt.show() 
