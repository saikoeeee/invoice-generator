# config.py

import os

SECRET_KEY = os.environ.get("SECRET_KEY", "invoicegenerator")
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "Your Business Name")
BUSINESS_EMAIL = os.environ.get("BUSINESS_EMAIL", "your@email.com")
BUSINESS_ADDRESS = os.environ.get("BUSINESS_ADDRESS", "Singapore")
BUSINESS_PHONE = os.environ.get("BUSINESS_PHONE", "+65 XXXX XXXX")
TAX_RATE = float(os.environ.get("TAX_RATE", "9.0"))