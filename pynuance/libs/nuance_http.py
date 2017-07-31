#!/usr/bin/env python

import json
import inspect

from requests.cookies import cookiejar_from_dict
import requests
from functools import wraps

from pynuance.libs.error import PyNuanceError


def _dev_login(username=None, password=None):
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
        raise PyNuanceError("Can not login to Nuance dev")
    return result.cookies


def _mix_login(username=None, password=None):
    # Login
    if username is None:
        username = input("Username: ")
    if password is None:
        password = input("Nuance dev password: ")

    headers = {"Content-Type": "application/json;charset=UTF-8"}
    data_login = {"username": username,
                  "password": password}
    url = "https://developer.nuance.com/mix/nlu/bolt/login"
    result = requests.post(url, data=json.dumps(data_login), headers=headers)
    if not result.json().get('status', False):
        raise PyNuanceError("Can not connect")
    return result.cookies


def nuance_login(website):
    def deco(func):
        @wraps(func)
        def wrapper(*args_, **kwargs_):
            # Get cookies
            func_args = inspect.getargspec(func)
            attr_dict = {"cookies_file": None,
                         "username": None,
                         "password": None,
                         }
            for attr in attr_dict:
                # Trying to get value in args
                if attr not in func_args.args:
                    error_msg = ("Can not use Nuance login decorator for `{}`"
                                 " function. Arg `{}` missing".format(func.__name__, attr))
                    raise PyNuanceError(error_msg)
                arg_ind = func_args.args.index(attr)
                try:
                    attr_dict[attr] = args_[arg_ind]
                except IndexError:
                    # Not found so set it as None
                    attr_dict[attr] = None
                if attr_dict[attr] is None:
                    # Trying to get value in kwargs
                    attr_dict[attr] = kwargs_.get(attr)

            if attr_dict["cookies_file"] is not None:
                # Using old cookies
                cookies = get_cookies(attr_dict["cookies_file"], website)
                func.__globals__['cookies'] = cookies
            else:
                # Trying to get cookies using username/password
                if website == "mix":
                    cookies = _mix_login(attr_dict.get('username'), attr_dict.get('password'))
                    func.__globals__['cookies'] = cookies
                elif website == "dev":
                    cookies = _dev_login(attr_dict.get('username'), attr_dict.get('password'))
                    func.__globals__['cookies'] = cookies
                else:
                    raise PyNuanceError("Bad website parameter")
            return func(*args_, **kwargs_)
        return wrapper
    return deco


def get_cookies(cookies_file, website):
    """Get cookies from saved file"""
    if website not in ("dev", "mix"):
        raise
    with open(cookies_file) as fhc:
        raw_cookies = json.load(fhc)
    if website not in raw_cookies:
        raise
    return cookiejar_from_dict(raw_cookies[website])
