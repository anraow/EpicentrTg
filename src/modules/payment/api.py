import requests
import json
# We import our db module, as it will be convenient to add from here
# transactions to the database
import db

# This is the beginning of our requests
TESTNET_API_BASE = "https://testnet.toncenter.com/api/v2/"

# Find out which network we are working on
with open('config.json', 'r') as f:
    config_json = json.load(f)
    TESTNET_API_TOKEN = config_json['TESTNET_API_TOKEN']
    TESTNET_WALLET = config_json['TESTNET_WALLET']
    WORK_MODE = config_json['WORK_MODE']


# Depending on the network, we take the necessary data.
if WORK_MODE == "testnet":
    API_BASE = TESTNET_API_BASE
    API_TOKEN = TESTNET_API_TOKEN
    WALLET = TESTNET_WALLET


def detect_address(address):
    url = f"{API_BASE}detectAddress?address={address}&api_key={API_TOKEN}"
    r = requests.get(url)
    response = json.loads(r.text)
    try:
        return response['result']['bounceable']['b64url']
    except:
        return False


def get_address_transactions():
    url = f"{API_BASE}getTransactions?address={WALLET}&limit=30&archival=true&api_key={API_TOKEN}"
    r = requests.get(url)
    response = json.loads(r.text)
    return response['result']



