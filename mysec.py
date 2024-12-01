import os
from dotenv import load_dotenv
load_dotenv()

TOKEN=os.getenv('TOKEN')
PHONE_ID=os.getenv('PHONE_ID')
MONGO_URI=os.getenv('MONGO_URI')
FB_TOKEN = os.getenv('FB_TOKEN')
VERSION = os.getenv('VERSION')

FACEBOOK_URL = f"https://crm.notbot.in/api/meta/{VERSION}/{PHONE_ID}/messages"

FACEBOOK_HEADERS = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {FB_TOKEN}'
                        }