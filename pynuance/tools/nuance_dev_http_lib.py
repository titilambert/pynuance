#!/usr/bin/env python

import json

import requests

def dev_login(username=None, password=None):
    """Login to Nuance developer page

    URL: https://developer.nuance.com/public/index.php
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if username is None:
        username = input("Username: ")
    if password is None:
        password = input("Nuance dev password: ")
    data_login = {"form": "login",
                  "command": "login",
                  "next": "",
                  "username": username,
                  "password": password,
                  "login": "",
                  }
    params = {"task": "login"}
    url = "https://developer.nuance.com/public/index.php"
    result = requests.post(url, data=data_login, params=params, allow_redirects=False)

    # Go to account page
    params = {"task": "account"}
    url = "https://developer.nuance.com/public/index.php"
    account_result = requests.get(url, params=params, cookies=result.cookies)

    if account_result.text.find("Edit My Profile") == -1:
        raise Exception("Can not login to Nuance dev")
    return result.cookies







def mix_login(username=None, password=None):
    # Login
    if username is None:
        username = input("Username: ")
    if password is None:
        password = input("Nuance dev password: ")

    headers = {"Content-Type": "application/json;charset=UTF-8"}
    data_login = {"username": username,
                  "password": password}
    result = requests.post("https://developer.nuance.com/mix/nlu/bolt/login", data=json.dumps(data_login), headers=headers)
    if not result.json().get('status', False):
        raise Exception("Can not connect")
    return result.cookies


