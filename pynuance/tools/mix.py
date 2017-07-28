#!/usr/bin/env python

import json

import requests
from bs4 import BeautifulSoup

from pynuance.tools.nuance_dev_http_lib import dev_login


def mix_available(username=None, password=None):

    # login
    cookies = dev_login(username, password)
    # Check mix status
    result = requests.get("https://developer.nuance.com/public/index.php", params={"task": "mix"}, cookies=cookies)

    # If "You're on the list!" is here, you just have to wait
    soup = BeautifulSoup(result.text, 'html.parser')
    waiting_node = soup.find("h4", text="You're on the list!")
    ok_node = soup.find("h4", text="Congratulations!")
    if waiting_node.parent.parent.parent.attrs.get('style') != 'display: none':
        print("The Mix team is working on your request, and it won't be long now...")
    elif ok_node.parent.parent.parent.attrs.get('style') != 'display: none':
        print("Your Mix account is activated, you can use NLU")
    else:
        print("You didn't activate MIX on your account.\n"
              "Go there https://developer.nuance.com/public/index.php?task=mix \n"
              "And ask for Nuance Mix.")
    # When is activated ????
