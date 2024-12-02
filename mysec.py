import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
VERSION = os.getenv('VERSION')


MONGO_URI=os.getenv('MONGO_URI')

FACEBOOK_URL = f"https://crm.notbot.in/api/meta/{VERSION}/{PHONE_NUMBER_ID}/messages"

FACEBOOK_HEADERS = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {TOKEN}'
                        }