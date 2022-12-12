import os

token = os.getenv('TOKEN')
WEBHOOK_PATH = "/telegram/cllpsticketsbot"
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
# webserver settings
WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 8000
