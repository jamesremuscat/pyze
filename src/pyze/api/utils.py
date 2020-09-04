import logging
import requests
from typing import Dict

_log = logging.getLogger("pyze.api.utils")


def get_api_keys_from_myrenault(locale="en_GB") -> Dict:
    url = f"https://renault-wrd-prod-1-euw1-myrapp-one.s3-eu-west-1.amazonaws.com/configuration/android/config_{locale}.json"
    print(url)
    response = requests.get(url)
    response.raise_for_status()
    response_body = response.json()

    _log.debug("Received api keys from myrenaul response: % s", response_body)

    servers = response_body["servers"]
    return {
        "gigya-api-key": servers["gigyaProd"]["apikey"],
        "gigya-api-url": servers["gigyaProd"]["target"],
        "kamereon-api-key": servers["wiredProd"]["apikey"],
        "kamereon-api-url": servers["wiredProd"]["target"],
    }
