import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API Credentials
# Get these from https://my.telegram.org/apps
API_ID = os.getenv("API_ID")
if API_ID:
    API_ID = int(API_ID)
    
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
SESSION_NAME = os.getenv("SESSION_NAME", "apsara_session")

# Bot API (for Login Widget & Notifications)
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_fixed_key_for_development")

# KHQR Payment Settings
KHQR_GLOBAL_ID = os.getenv("KHQR_GLOBAL_ID", "phannith@bkrt")
KHQR_MERCHANT_ID = os.getenv("KHQR_MERCHANT_ID", "85587991194") # Phone/Account without +
KHQR_MERCHANT_NAME = os.getenv("KHQR_MERCHANT_NAME", "NOY PHANNITH")

