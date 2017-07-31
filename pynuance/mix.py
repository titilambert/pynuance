#!/usr/bin/env python

import json
import time

import requests
from bs4 import BeautifulSoup

from pynuance.libs.nuance_http import nuance_login
from pynuance.libs.languages import LANGUAGES
from pynuance.libs.error import PyNuanceError


@nuance_login("dev")
def mix_activated(username=None, password=None, cookies_file=None):
    """Check if the account has access to Nuance Mix.

    URL: https://developer.nuance.com/mix/nlu/#/models/

    :returns: * 0 means Mix account activated.
              * 1 means Mix is being created
              * 2 means demand not done. You have to connect to Nuance website and ask for it
    :rtype: int
    """
    # Check mix status
    result = requests.get("https://developer.nuance.com/public/index.php", params={"task": "mix"}, cookies=cookies)

    # If "You're on the list!" is here, you just have to wait
    soup = BeautifulSoup(result.text, 'html.parser')
    waiting_node = soup.find("h4", text="You're on the list!")
    ok_node = soup.find("h4", text="Congratulations!")

    if ok_node.parent.parent.parent.attrs.get('style') != 'display: none':
        return 0
    elif waiting_node.parent.parent.parent.attrs.get('style') != 'display: none':
        return 1
    else:
        return 2


@nuance_login("mix")
def list_models(username=None, password=None, cookies_file=None):
    """Get list of models/project from Nuance Mix."""
    result = requests.get("https://developer.nuance.com/mix/nlu/api/v1/projects", cookies=cookies)
    return result.json().get("data", [])
    # {'name': 'coffeeMaker', 'type': {}, 'stats': {'ontology': {'nbOntologyIntents': 2, 'nbOntologyMentions': 20, 'nbPatterns': 24}, 'nlu': {'verified': 37, 'size': 37}}, 'metadata': {'source': ['Nuance Communications'], 'type': ['sample'], 'version': ['2.0.0'], 'description': ['Sample model for demonstration of 1 simple intent and two concepts'], 'created_by': ['titilambert@gmail.com', 'Thibault Cohen'], 'short_name': ['Coffee Maker Sample Model'], 'last_saved': ['Fri Jul 28 23:37:37 UTC 2017'], 'created_at': ['2017-07-28 20:55:09+00:00']}, 'locale': 'en_US', 'loaded': False, 'languageDomainTopic': 'nma', 'ontology': {'version': '', 'isLoaded': False}, 'sources': [{'name': 'nuance_custom_data', 'version': '1.0', 'displayName': 'nuance_custom_data', 'type': 'CUSTOM'}], 'created': '2017-07-28T20:55:10.156244Z', 'id': 6965}


@nuance_login("mix")
def create_model(name, language, username=None, password=None, cookies_file=None):
    """Create a new model in Nuance Mix."""
    # Check language
    voices_by_lang = dict([(l['code'], l['voice']) for l in LANGUAGES.values()])
    if language not in voices_by_lang:
        raise PyNuanceError("Error: language should be in {}".format(', '.join(voices_by_lang.keys())))
    # First request
    data = {"name": name,
            "domains": [],
            "locale": language,
            "sources": []}
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    result = requests.post("https://developer.nuance.com/mix/nlu/api/v1/projects", data=json.dumps(data), cookies=cookies, headers=headers)
    if result.status_code  != 200:
        raise PyNuanceError("Unknown HTTP error on the first request")
    model_json = result.json()
    model_id = model_json.get("id")
    if model_id is None:
        raise PyNuanceError("The HTTP create request did not return the new model ID")
        #{"id": 6967, "name": "MODELNAME", "created": "2017-07-28T22:27:03.253884Z", "builds": [], "collaborators": [{"id": 6344, "name": "Thibault Cohen", "first_name": "Thibault", "last_name": "Cohen", "email": "titilambert@gmail.com", "telephone_num": null, "created_at": "2017-07-27T20:00:04.140590Z", "last_logged_in": "2017-07-28T20:54:20.902053Z", "thumbnail_url": "//www.gravatar.com/avatar/1e569dd79391d30b362b399c2629ac6e?d=https%3A%2F%2Fdeveloper.nuance.com%2Fmix%2Fnlu%2Fimages%2Fdefault_avatar_1.png&s=150", "lang": "en", "is_super_admin": false, "companies": []}], "owners": [6344], "domains": [], "notes": null, "languageDomainTopic": "nma", "locale": "en_US", "stats": {"ontology": {"nbPatterns": 0, "nbOntologyIntents": 1, "nbOntologyMentions": 18}, "nlu": {"verified": 0, "size": 0}}}
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
    result = requests.post("https://developer.nuance.com/mix/nlu/bolt/ubt", data=json.dumps(data), cookies=cookies)
    res_json = result.json()
    if res_json != {}:
        raise PyNuanceError("Unknown HTTP error on the second request")
    # Third request
    url_put_3 = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id)
    requests.put(url_put_3, cookies=cookies)
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
            "page":"/model/{}/dashboard".format(model_id),
            "query_params":{},
            "host":"developer.nuance.com",
            "port":"",
            "protocol":"https",
            "category":"model",
            "action":"delete",
            "label":"cancelled",
            "value": model_id}

    result = requests.post("https://developer.nuance.com/mix/nlu/bolt/ubt", data=json.dumps(data), cookies=cookies)
    
    if result.status_code != 200:
        raise

    result = requests.delete("https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id), cookies=cookies)
    if result.status_code != 204:
        raise


@nuance_login("mix")
def upload_model(name, model_file, username=None, password=None, cookies_file=None):
    """Upload intent file into a Mix model"""
    # Get 
    model_id = get_model_id(name, username, password, cookies_file)

    # Send file
    with open(model_file) as fhm:
        print("Sending: {}".format(model_file))
        url = "https://developer.nuance.com/mix/nlu/api/v1/data/{}/import".format(model_id)
        files = {'file': open(model_file, 'rb')}
        result = requests.post(url, files=files, cookies=cookies)

    # Save
    url = "https://developer.nuance.com/mix/nlu/api/v1/project/{}".format(model_id)
    requests.put(url, cookies=cookies)
    time.sleep(1)


@nuance_login("mix")
def train_model(name, username=None, password=None, cookies_file=None):
    print("Training: {}".format(name))
    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)

    url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/annotations/train".format(model_id)
    requests.post(url, cookies=cookies)
    time.sleep(1)


@nuance_login("mix")
def get_model(name, username=None, password=None, cookies_file=None):

    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)

    url = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id)
    result = requests.get(url, cookies=cookies)
    return result.json()


def model_build_create(name, notes="", username=None, password=None, cookies_file=None):
    """Create a new model build."""
    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)
    # Send Request
    url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/engine".format(model_id)
    params = {"notes": notes, "type": "Default", "with_asr": "true"}
    requests.post(url, params=params, cookies=cookies)
    # TODO check build status each second to wait completion


def model_build_list(name, username=None, password=None, cookies_file=None):
    """Return the list of all builds for a given model"""
    model = get_model(name, username, password, cookies_file)
    return model.get("builds", [])


@nuance_login("mix")
def model_build_attach(name, build_version=None, context_tag="latest", username=None, password=None, cookies_file=None):
    """Attach model version to a Nuance App

    For now, only SandBoxApp is supported by pynuance
    """
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
    result = requests.get(url, params=params, cookies=cookies)
    app_id = None
    for app in result.json().get("applications"):
        if app['name'] == 'Sandbox App':
            app_id = app['id']
            break
    # Get NMAID
    url = "https://developer.nuance.com/mix/nlu/bolt/nmaids"
    result = requests.get(url, cookies=cookies)
    nmaids = [app['nmaid'] for app in result.json()['data'] if app['app_id'] == app_id]
    if len(nmaids) < 1:
        raise PyNuanceError("Can not get nmaid")
    nmaid = nmaids[0]
    # Attach
    data = {"nmaid": nmaid,
            "project_id": model_id, "tag": context_tag}
    url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations".format(app_id)
    result = requests.post(url, data=json.dumps(data), cookies=cookies, headers=headers)
    conf_id = result.json().get("id")
    if conf_id is None:
        raise PyNuanceError("Can not find configuration ID")

    data = {"page": "/model/{}/publish".format(model_id),
            "query_params": {},
            "host":"developer.nuance.com",
            "port":443,
            "protocol":"https",
            "category":"publish",
            "action":"associate-to-app",
            "label":"finish",
            "value":""}
    url = "https://developer.nuance.com/mix/nlu/bolt/ubt"
    result = requests.post(url, data=json.dumps(data), cookies=cookies, headers=headers)

    url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations/{}/settings".format(app_id, conf_id)
    result = requests.put(url, data=json.dumps({}), cookies=cookies, headers=headers)

    url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations/{}/models".format(app_id, conf_id)
    if build_id is not None:
        data = [{"model_id": "{}".format(model_id),
                 "build_id": "{}".format(build_id),
                 "build_version": "{}".format(build_version)}]
    else:
        data = [{"model_id": "{}".format(model_id)}]
    requests.put(url, data=json.dumps(data), cookies=cookies, headers=headers)
