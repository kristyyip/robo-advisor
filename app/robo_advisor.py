import csv
import json
import os

from datetime import datetime, timedelta

from dotenv import load_dotenv
import requests

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from twilio.rest import Client

import matplotlib.pyplot as plt
import pandas as pd

def to_usd(my_price):
    """
    Converts a numeric value to usd-formatted string, for printing and display purposes.
    
    Source: https://github.com/prof-rossetti/intro-to-python/blog/master/notes/python/datatypes/numbers.
    
    Param: my_price (int or float) like 4000.444444
    
    Example: to_usd(4000.444444)
    
    Returns: $4,000.44
    """
    return "${0:,.2f}".format(my_price)

def transform_response(parsed_response):
    """
    Creates a list of dictionaries of stock price information from retrieved data from JSON file
    Param: parsed_response (dict), which representing the original JSON response
        It should have keys: "Meta Data" and "Time Series Daily"
    Example: transform_response(parsed_response)
    Returns: rows
        # the following is an example if parsed_response contained dictionaries of the following information
        [
            {"timestamp": "2019-06-08", "open": "101.0924", "high": "101.9500", "low": "100.5400", "close": "101.6300", "volume": "22165128"},
            {"timestamp": "2019-06-07", "open": "102.6500", "high": "102.6900", "low": "100.3800", "close": "100.8800", "volume": "28232197"},
            {"timestamp": "2019-06-06", "open": "102.4800", "high": "102.6000", "low": "101.9000", "close": "102.4900", "volume": "21122917"},
        ]
    """
    tsd = parsed_response["Time Series (Daily)"]

    rows = []
    for date, daily_prices in tsd.items(): # see: https://github.com/prof-rossetti/georgetown-opim-243-201901/blob/master/notes/python/datatypes/dictionaries.md
        row = {
            "timestamp": date,
            "open": float(daily_prices["1. open"]),
            "high": float(daily_prices["2. high"]),
            "low": float(daily_prices["3. low"]),
            "close": float(daily_prices["4. close"]),
            "volume": int(daily_prices["5. volume"])
        }
        rows.append(row)

    return rows

def write_to_csv(rows, csv_filepath):
    """
    Writes information into a .csv file

    Param: rows (list) and csv_filepath (str, should lead to a .csv file within the directory where the data will be written)

    Example: write_to_csv(example_rows, csv_file_path)

    Returns: True
    """
    csv_headers = ["timestamp", "open", "high", "low", "close", "volume"]

    with open(csv_filepath, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
        writer.writeheader() # uses fieldnames set above
        for row in rows:
            writer.writerow(row)
    
    return True

if __name__ == "__main__":
    
    load_dotenv()

    #
    # INFO INPUTS
    #

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    symbol = input("Please choose a valid stock symbol to evaluate (i.e. MSFT): ") # accept user input
    length = len(symbol) # to retrieve the length of the user's input
    request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"

    # validating user's input by checking to see if it is all letters or 1-5 characters
    if symbol.isdigit() or (length < 1 or length > 5): # source for letter/number check: https://pynative.com/python-check-user-input-is-number-or-string/
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

        # retrieve data from json file
        parsed_response = json.loads(response.text)

        last_refreshed = parsed_response["Meta Data"]["3. Last Refreshed"]

        rows = transform_response(parsed_response)

        latest_day = rows[0]["timestamp"]
        latest_close = rows[0]["close"]

        
        # maximum of all high prices
        high_prices = []
        low_prices = []

        for row in rows:
            high_price = row["high"]
            low_price = row["low"]
            high_prices.append(float(high_price))
            low_prices.append(float(low_price))

        recent_high = max(high_prices)
        recent_low = min(low_prices)

        # sending alerts 
        ## via email 
        current_datetime = datetime.now() # source: tecadmin.net/get-current-date-time-python/
        second_latest_close = rows[1]["close"]
        second_latest_day = rows[1]["timestamp"]
        timestamp = current_datetime.strftime("%B %d, %Y at %I:%M %p")

        while True:
            email_choice = input("Would you like to receive an email alerting you about price movements? (Yes or No): ") # accept user's input

            if email_choice.lower() == "yes": # email alerts if user's input is "yes"
                print("Great! You'll receive an email if there was a price movement within the past day of the latest day's stock.")

                if (float(latest_close) < .95*(float(second_latest_close))): # send email if latest closing price decreased by more than 5% within the past day of the latest day's stock
                    SENDGRID_API_KEY = os.environ.get("SENDGRID_API", "OOPS, please set env var called 'SENDGRID_API'")
                    MY_ADDRESS = os.environ.get("MY_EMAIL", "OOPS, please set env var called 'MY_EMAIL'")

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
                elif (float(latest_close) > 1.05*(float(second_latest_close))):  # send email if latest closing price increased by more than 5% within the past day of the latest day's stock
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
                else: # don't do anything if closing price within 5% above or below within the past day of the latest day's stock
                    break
            elif email_choice.lower() == "no": # no email alerts if user says "no"
                print("Okay, you will not receive any email alerts for price movements.")
                break
            else: # invalid input if user puts something other than "yes" or "no"
                print("Sorry, that isn't a valid choice. Please choose 'Yes' or 'No'.")

        ## via SMS
        while True:
            SMS_choice = input("Would you like to receive a text alerting you about price movements? (Yes or No): ") # accept user's input

            if SMS_choice.lower() == "yes": # SMS alerts if user's input is "yes"
                print("Great! You'll receive a text if there was a price movement within the past day of the latest day's stock.")
                
                TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "OOPS, please specify env var called 'TWILIO_ACCOUNT_SID'")
                TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN", "OOPS, please specify env var called 'TWILIO_AUTH_TOKEN'")
                SENDER_SMS  = os.environ.get("SENDER_SMS", "OOPS, please specify env var called 'SENDER_SMS'")
                RECIPIENT_SMS  = os.environ.get("RECIPIENT_SMS", "OOPS, please specify env var called 'RECIPIENT_SMS'")

                # AUTHENTICATE

                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

                if (float(latest_close) < .95*(float(second_latest_close))): # send SMS if latest closing price decreased by more than 5% within the past day of the latest day's stock
                    # COMPILE REQUEST PARAMETERS (PREPARE THE MESSAGE)
                    content = f"PRICE MOVEMENT ALERT: Hello, this is a PRICE DECREASE alert for {symbol} from Robo Advisor. The price has decreased by more than 5% within the past day of the latest day's stock. The closing price for {second_latest_day} was {second_latest_close}, decreasing to {latest_close} for {last_refreshed}. Thank you for using Robo Advisor."

                    # ISSUE REQUEST (SEND SMS)
                    message = client.messages.create(to=RECIPIENT_SMS, from_=SENDER_SMS, body=content)

                    # PARSE RESPONSE
                    print("----------------------")
                    print("SMS")
                    print("----------------------")
                    print("RESPONSE: ", type(message))
                    print("FROM:", message.from_)
                    print("TO:", message.to)
                    print("BODY:", message.body)
                    print("PROPERTIES:")
                    print(message._properties)

                    break
                elif (float(latest_close) > 1.05*(float(second_latest_close))): # send SMS if latest closing price increased by more than 5% within the past day of the latest day's stock
                    # COMPILE REQUEST PARAMETERS (PREPARE THE MESSAGE)
                    content = f"PRICE MOVEMENT ALERT: Hello, this is a PRICE INCREASE alert for {symbol} from Robo Advisor. The price has increased by more than 5% within the past day of the latest day's stock. The closing price for {second_latest_day} was {second_latest_close}, increasing to {latest_close} for {last_refreshed}. Thank you for using Robo Advisor."

                    # ISSUE REQUEST (SEND SMS)
                    message = client.messages.create(to=RECIPIENT_SMS, from_=SENDER_SMS, body=content)

                    # PARSE RESPONSE
                    print("----------------------")
                    print("SMS")
                    print("----------------------")
                    print("RESPONSE: ", type(message))
                    print("FROM:", message.from_)
                    print("TO:", message.to)
                    print("BODY:", message.body)
                    print("PROPERTIES:")
                    print(message._properties)

                    break
                else: # don't do anything if closing price within 5% above or below within the past day of the latest day's stock
                    break
            elif SMS_choice.lower() == "no": # no SMS alerts if user says "no"
                print("Okay, you will not receive any texts for price movements.")
                break
            else: # invalid input if user puts something other than "yes" or "no"
                print("Sorry, that isn't a valid choice. Please choose 'Yes' or 'No'.")

            
        #
        # INFO OUTPUTS
        #

        # csv_file_path = "data/prices.csv"
        ## creating a csv file of the stock prices
        csv_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "prices.csv")

        write_to_csv(rows, csv_file_path)

        #print outputs
        print("-------------------------")
        print(f"SELECTED SYMBOL: {symbol}")
        print("-------------------------")
        print("REQUESTING STOCK MARKET DATA...")

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

        ax1.plot(stock_prices['open'], 'r')
        ax2.plot(stock_prices['high'], 'b')
        ax3.plot(stock_prices['low'], 'g')
        ax4.plot(stock_prices['close'], 'k')

        ## setting subplot labels
        ax1.set_title(f'Opening Stock Prices Over Time for {symbol}')
        ax2.set_title(f'High Stock Prices Over Time for {symbol}')
        ax3.set_title(f'Low Stock Prices Over Time for {symbol}')
        ax4.set_title(f'Closing Stock Prices Over Time for {symbol}')

        ax3.set_xlabel('Day')
        ax4.set_xlabel('Day')
        ax1.set_ylabel('Price')
        ax3.set_ylabel('Price')

        plt.show() # generate subplots
