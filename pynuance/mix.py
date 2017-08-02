"""Provides functions to interacte with Nuance Mix Website"""
import json
import time

import requests
from bs4 import BeautifulSoup

from pynuance.libs.nuance_http import nuance_login
from pynuance.libs.languages import LANGUAGES
from pynuance.libs.error import PyNuanceError


@nuance_login("dev")
def mix_activated(username=None, password=None, cookies_file=None):  # pylint: disable=W0613
    """Check if the account has access to Nuance Mix.

    URL: https://developer.nuance.com/mix/nlu/#/models/

    :returns: * True means Mix account activated.
              * False means Mix is being created or not requested
    :rtype: bool
    """
    # Check mix status
    url = "https://developer.nuance.com/public/index.php"
    result = requests.get(url, params={"task": "mix"},
                          cookies=cookies)  # pylint: disable=E0602

    # If "You're on the list!" is here, you just have to wait
    soup = BeautifulSoup(result.text, 'html.parser')
    waiting_node = soup.find("h4", text="You're on the list!")
    ok_node = soup.find("h4", text="Congratulations!")

    if waiting_node.parent.parent.parent.attrs.get('style') != 'display: none':
        return False
    elif ok_node.parent.parent.parent.attrs.get('style') != 'display: none':
        return True
    else:
        raise PyNuanceError("Mix account state unknown")


@nuance_login("mix")
def list_models(username=None, password=None, cookies_file=None):  # pylint: disable=W0613
    """Get list of models/project from Nuance Mix."""
    result = requests.get("https://developer.nuance.com/mix/nlu/api/v1/projects",
                          cookies=cookies)  # pylint: disable=E0602
    return result.json().get("data", [])


@nuance_login("mix")
def create_model(name, language,
                 username=None, password=None, cookies_file=None):  # pylint: disable=W0613
    """Create a new model in Nuance Mix."""
    # Check language
    voices_by_lang = dict([(l['code'], l['voice']) for l in LANGUAGES.values()])
    if language not in voices_by_lang:
        raise PyNuanceError("Error: language should be in "
                            "{}".format(', '.join(voices_by_lang.keys())))
    # First request
    data = {"name": name,
            "domains": [],
            "locale": language,
            "sources": []}
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    url = "https://developer.nuance.com/mix/nlu/api/v1/projects"
    result = requests.post(url, data=json.dumps(data), headers=headers,
                           cookies=cookies)  # pylint: disable=E0602
    if result.status_code != 200:
        raise PyNuanceError("Unknown HTTP error on the first request")
    model_json = result.json()
    model_id = model_json.get("id")
    if model_id is None:
        raise PyNuanceError("The HTTP create request did not return the new model ID")
    # Second request
    data = {"session_id": "-1",
            "project_id": "-1",
            "page": "/models/",
            "query_params": {},
            "host": "developer.nuance.com",
            "port": "",
            "protocol": "https",
            "category": "model",
            "action": "create",
            "label": name,
            "value": ""}
    url = "https://developer.nuance.com/mix/nlu/bolt/ubt"
    result = requests.post(url, data=json.dumps(data),
                           cookies=cookies)  # pylint: disable=E0602
    res_json = result.json()
    if res_json != {}:
        raise PyNuanceError("Unknown HTTP error on the second request")
    # Third request
    url_put_3 = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id)
    requests.put(url_put_3,
                 cookies=cookies)  # pylint: disable=E0602

    # Result model
    return model_json


def get_model_id(name, username=None, password=None, cookies_file=None):
    """Get model ID from model name.

    If name is already a model ID, this function can help to validate the existance of the model.

    Raise if there are 2 or more models with the same name.
    """
    models = list_models(username, password, cookies_file)

    model_id = None
    for model in models:
        if model.get("name") == name and model_id is not None:
            raise PyNuanceError("There at least two models with the same name. "
                                "Please use the model ID instead")
        elif model.get("name") == name:
            model_id = model.get("id")
        try:
            if model.get("id") == int(name):
                model_id = int(name)
                break
        except ValueError:
            pass
    if model_id is None:
        raise PyNuanceError("Model '{}' not found".format(name))

    return model_id


@nuance_login("mix")
def delete_model(name, username=None, password=None, cookies_file=None):
    """Delete a model from model name or model ID"""
    model_id = get_model_id(name, username, password, cookies_file)

    data = {"session_id": "-1",
            "project_id": "-1",
            "page": "/model/{}/dashboard".format(model_id),
            "query_params": {},
            "host": "developer.nuance.com",
            "port": "",
            "protocol": "https",
            "category": "model",
            "action": "delete",
            "label": "cancelled",
            "value": model_id}

    url = "https://developer.nuance.com/mix/nlu/bolt/ubt"
    result = requests.post(url, data=json.dumps(data),
                           cookies=cookies)  # pylint: disable=E0602

    if result.status_code != 200:
        raise PyNuanceError("Bad HTTP status code during the model deletion")

    url = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id)
    result = requests.delete(url,
                             cookies=cookies)  # pylint: disable=E0602

    if result.status_code != 204:
        raise PyNuanceError("Bad HTTP status code during the model deletion")


@nuance_login("mix")
def upload_model(name, model_file, username=None, password=None, cookies_file=None):
    """Upload intent file into a Mix model."""
    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)

    # Send file
    with open(model_file, 'rb') as fhm:
        print("Sending: {}".format(model_file))
        url = "https://developer.nuance.com/mix/nlu/api/v1/data/{}/import".format(model_id)
        files = {'file': fhm}
        requests.post(url, files=files,
                      cookies=cookies)  # pylint: disable=E0602

    # Save
    url = "https://developer.nuance.com/mix/nlu/api/v1/project/{}".format(model_id)
    requests.put(url,
                 cookies=cookies)  # pylint: disable=E0602
    time.sleep(1)


@nuance_login("mix")
def train_model(name, username=None, password=None, cookies_file=None):
    """Train a given Mix Model"""
    print("Training: {}".format(name))
    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)

    url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/annotations/train".format(model_id)
    requests.post(url,
                  cookies=cookies)  # pylint: disable=E0602


@nuance_login("mix")
def get_model(name, username=None, password=None, cookies_file=None):
    """Get model data from Nuance Mix Website"""
    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)

    url = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id)
    result = requests.get(url,
                          cookies=cookies)  # pylint: disable=E0602
    return result.json()


def model_build_create(name, notes="", username=None, password=None, cookies_file=None):
    """Create a new model build."""
    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)
    # Send Request
    url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/engine".format(model_id)
    params = {"notes": notes, "type": "Default", "with_asr": "true"}
    requests.post(url, params=params,
                  cookies=cookies)  # pylint: disable=E0602
    # TODO check build status each second to wait completion


def model_build_list(name, username=None, password=None, cookies_file=None):
    """Return the list of all builds for a given model"""
    model = get_model(name, username, password, cookies_file)
    return model.get("builds", [])


@nuance_login("mix")
def model_build_attach(name, build_version=None, context_tag="latest",
                       username=None, password=None, cookies_file=None):
    """Attach model version to a Nuance App

    For now, only SandBoxApp is supported by pynuance
    """
    # TODO validate context_tag
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    # Get model ID
    model = get_model(name, username, password, cookies_file)
    model_id = model.get("id")
    # Get buildID
    build_id = None
    if build_version is not None:
        for build in model.get("builds", []):
            if int(build_version) == build.get("version"):
                build_id = build.get("id")
                break
        if build_id is None:
            raise Exception("Build not found")
    # Get SandBox app ID
    url = "https://developer.nuance.com/mix/nlu/bolt/applications"
    params = {"configurations": "true"}
    result = requests.get(url, params=params,
                          cookies=cookies)  # pylint: disable=E0602
    app_id = None
    for app in result.json().get("applications"):
        if app['name'] == 'Sandbox App':
            app_id = app['id']
            break
    # Get NMAID
    url = "https://developer.nuance.com/mix/nlu/bolt/nmaids"
    result = requests.get(url,
                          cookies=cookies)  # pylint: disable=E0602
    nmaids = [app['nmaid'] for app in result.json()['data'] if app['app_id'] == app_id]
    if len(nmaids) < 1:
        raise PyNuanceError("Can not get nmaid")
    nmaid = nmaids[0]
    # Attach
    data = {"nmaid": nmaid,
            "project_id": model_id, "tag": context_tag}
    url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations".format(app_id)
    result = requests.post(url, data=json.dumps(data), headers=headers,
                           cookies=cookies)  # pylint: disable=E0602
    conf_id = result.json().get("id")
    if conf_id is None:
        raise PyNuanceError("Can not find configuration ID")

    data = {"page": "/model/{}/publish".format(model_id),
            "query_params": {},
            "host": "developer.nuance.com",
            "port": 443,
            "protocol": "https",
            "category": "publish",
            "action": "associate-to-app",
            "label": "finish",
            "value": ""}
    url = "https://developer.nuance.com/mix/nlu/bolt/ubt"
    result = requests.post(url, data=json.dumps(data), headers=headers,
                           cookies=cookies)  # pylint: disable=E0602

    url = ("https://developer.nuance.com/mix/nlu/bolt/applications/{}/"
           "configurations/{}/settings".format(app_id, conf_id))
    result = requests.put(url, data=json.dumps({}), headers=headers,
                          cookies=cookies)  # pylint: disable=E0602

    url = ("https://developer.nuance.com/mix/nlu/bolt/applications/{}/"
           "configurations/{}/models".format(app_id, conf_id))
    if build_id is not None:
        data = [{"model_id": "{}".format(model_id),
                 "build_id": "{}".format(build_id),
                 "build_version": "{}".format(build_version)}]
    else:
        data = [{"model_id": "{}".format(model_id)}]
    requests.put(url, data=json.dumps(data), headers=headers,
                 cookies=cookies)  # pylint: disable=E0602
