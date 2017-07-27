#!/usr/bin/env python

import json

import requests
from bs4 import BeautifulSoup

from pynuance.tools.nuance_dev_http_lib import dev_login


def get_credentials(username=None, password=None, credential_file=None):
    """Get credentials from Nuance dev page"""
    credentials = {"appId": None,
                   "appKey": None,
                   }
    # login
    cookies = dev_login(username, password)
    # Go to sandbox page to get credentials
    result = requests.get("https://developer.nuance.com/public/index.php", params={"task": "credentials"}, cookies=cookies)
    soup = BeautifulSoup(result.text, 'html.parser')
    # Get app id
    appid_label_node = soup.find('label', text="App Id")
    credentials["appId"] = appid_label_node.parent.text.replace("App Id", "").strip()
    # Get app key
    appkey_label_node = soup.find('label', text="App Key")
    credentials["appKey"] = appkey_label_node.parent.find("code").text.strip()
    if credential_file is None:
        # Print credentials
        print("App Id:  {}".format(credentials["appId"]))
        print("App Key: {}".format(credentials["appKey"]))
    else:
        # Save credentials in a file
        with open(credential_file, "w") as fhc:
            json.dump(credentials, fhc)

