import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def generate_twiml_for_stream(stream_url: str):
    """Generate TwiML to start a Media Stream."""
    response = VoiceResponse()
    connect = Connect()
    stream = Stream(url=stream_url)
    connect.append(stream)
    response.append(connect)
    return str(response)

def make_outbound_call(to_number: str, stream_url: str):
    """Initiate an outbound call that connects to the media stream."""
    twiml = generate_twiml_for_stream(stream_url)
    
    call = client.calls.create(
        twiml=twiml,
        to=to_number,
        from_=TWILIO_PHONE_NUMBER
    )
    return call.sid
