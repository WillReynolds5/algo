import os
from twilio.rest import Client


# Your Account Sid and Auth Token from twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)


message = client.messages \
    .create(
    body="What up bitches, "
         "welcome to the boys automated crypto notication service. "
         "Our algo is live 24/7 monitoring the market. Everytime a crypto gets overbought or oversold by a hedgefund, "
         "we will notify you immedietly for profiting off market reversal. "
         "Once the notification comes in, we recommend you buy the asset immedietly and sell within 30 mins - 2 hours. "
         "The signal will likely come in once every 7-10 days. "
         "Good Luck. - Simple Pump",
    from_='+16787125007',
    to='+16177943074'
)


print(message.sid)