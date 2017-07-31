"""Manage Nuance credentials and cookies"""
import json

import requests
from bs4 import BeautifulSoup

from pynuance.libs.nuance_http import nuance_login, _dev_login, _mix_login
from pynuance.libs.error import PyNuanceError
from pynuance.mix import mix_activated


@nuance_login("dev")
def get_credentials(username=None, password=None, cookies_file=None):  # pylint: disable=W0613
    """Get credentials from Nuance dev page"""
    credentials = {"appId": None,
                   "appKey": None,
                   }
    # Go to sandbox page to get credentials
    url = "https://developer.nuance.com/public/index.php"
    # pylint: disable=E0602
    result = requests.get(url, params={"task": "credentials"}, cookies=cookies)
    # pylint: enable=E0602
    if result.status_code != 200:
        raise PyNuanceError("Can not go to {}".format(url))
    # parse html page
    soup = BeautifulSoup(result.text, 'html.parser')
    # Get app id
    appid_label_node = soup.find('label', text="App Id")
    if appid_label_node is None:
        raise PyNuanceError("Can not go to {}".format(url))
    credentials["appId"] = appid_label_node.parent.text.replace("App Id", "").strip()
    # Get app key
    appkey_label_node = soup.find('label', text="App Key")
    credentials["appKey"] = appkey_label_node.parent.find("code").text.strip()
    return credentials


def save_cookies(cookies_file, username=None, password=None):
    """Login Dev and Mix Nuance web sites and save cookies to the disk"""
    # login to Nuance dev
    tmp_cookies = _dev_login(username, password)
    dev_cookies = tmp_cookies.get_dict()
    # Saving cookies
    cookies = {"dev": dev_cookies}
    with open(cookies_file, "w") as fhc:
        fhc.write(json.dumps(cookies))
    # Check if Nuance Mix is activated
    if mix_activated(None, None, cookies_file) != 0:
        # login to Nuance Mix
        tmp_cookies = _mix_login(username, password)
        mix_cookies = tmp_cookies.get_dict()
        # Saving cookies
        cookies = {"dev": dev_cookies,
                   "mix": mix_cookies}
        with open(cookies_file, "w") as fhc:
            fhc.write(json.dumps(cookies))
    # TODO if not, logit
