#!/usr/bin/env python

import json

import requests
from requests.cookies import cookiejar_from_dict
from bs4 import BeautifulSoup

from pynuance.libs.nuance_http import nuance_login


@nuance_login("dev")
def get_credentials(username=None, password=None, cookies_file=None, credential_file=None):
    """Get credentials from Nuance dev page"""
    credentials = {"appId": None,
                   "appKey": None,
                   }
    # Go to sandbox page to get credentials
    result = requests.get("https://developer.nuance.com/public/index.php", params={"task": "credentials"}, cookies=cookies)
    if result.status_code != 200:
        raise
    soup = BeautifulSoup(result.text, 'html.parser')
    # Get app id
    appid_label_node = soup.find('label', text="App Id")
    if appid_label_node is None:
        raise
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


def save_cookies(cookies_file, username=None, password=None):
    """Login Dev and Mix Nuance web sites and save cookies to the disk"""
    # login
    tmp_cookies = dev_login(username, password)
    dev_cookies = tmp_cookies.get_dict()
    tmp_cookies = mix_login(username, password)
    mix_cookies = tmp_cookies.get_dict()
    cookies = {"dev": dev_cookies,
               "mix": mix_cookies}
    with open(cookies_file, "w") as fhc:
        fhc.write(json.dumps(cookies))
