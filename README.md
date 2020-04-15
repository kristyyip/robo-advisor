# robo-advisor project

[Project Description](https://github.com/prof-rossetti/intro-to-python/blob/master/projects/robo-advisor/README.md)

## Installation

Clone or download from [GitHub Source](https://github.com/kristyyip/robo-advisor) onto your computer, choosing a familiar download location like the Desktop. 

Then navigate into the project repository from the command-line:

```sh
cd ~/Desktop/robo-advisor
```

## Environment Variable Setup

### AlphaVantage API Key
Before using or developing this application, take a moment to [obtain an AlphaVantage API Key](https://www.alphavantage.co/support/#api-key) (e.g. "abc123").

After obtaining an API Key, create a new file in this repository called ".env" (hidden by the .gitignore file), and update the contents of the ".env" file to specify your real API Key in an enviornment variable:

    ALPHAVANTAGE_API_KEY="abc123"

### SendGrid / Email Capabilities
Additionally, take a moment to [create an API Key](https://app.sendgrid.com/settings/api_keys) with "full access permissions on SendGrid. You may need to sign up for an account if you haven't done so already.

After obtaining an API Key, update the contents of the ".env" file to specify your real API Key in an environment variable:

    SENDGRID_API="abc123"

You will also need to update the contents of the ".env" file to specify your email address that is associated with your SendGrid account in an enviornment variable:
    
    MY_EMAIL="abc123@gmail.com"

### Twilio / SMS Capabilities
Lastly, take a moment to [create a new project](https://www.twilio.com/console/projects/create) with "Programmable SMS" capabilities on Twilio. You may need to sign up for an account if you haven't done so already. From the console, view that project's Account SID and Auth Token. Update the contents of the ".env" file to specify these values as environment variables:
    
    TWILIO_ACCOUNT_SID="abc123"
    TWILIO_AUTH_TOKEN="abc123"

You'll also need to [obtain a Twilio phone number](https://www.twilio.com/console/sms/getting-started/build) to send the messages from. After doing so, update the contents of the ".env" file to specify this value (including the plus sign at the beginning) as an environment variable:
    
    SENDER_SMS="+11234567890"

Finally, set an environment variable to specify the recipient's phone number (including the plus sign at the beginning):
    
    RECIPIENT_SMS="+11234567890"

## Virtual Environment Setup
Create and activate a new Anaconda virtual environment from the command-line:

```sh
conda create -n stocks-env python=3.7 # (first time only)
conda activate stocks-env
```

From inside the virtual environment, install the package dependencies specified in the "requirements.txt" file that is included in this repository:

```sh
pip install -r requirements.txt
```

## Additional Setup
Within the sub-directory "data", add a prices.csv file. This should be hidden by the .gitignore file in that sub-directory.

## Usage

Run the program:

```sh
python app/robo-advisor.py
```

## Testing

Install the `pytest` package, perhaps within a virtual environment:

```sh
pip install pytest
```

Run tests:

```py
pytest