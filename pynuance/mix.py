#!/usr/bin/env python

import json
import time

import requests
from bs4 import BeautifulSoup

from pynuance.libs.nuance_http import nuance_login
from pynuance.libs.languages import LANGUAGES

@nuance_login("dev")
def mix_available(username=None, password=None, cookies_file=None):

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

@nuance_login("mix")
def create_model(name, language, username=None, password=None, cookies_file=None):
    # Check language
    voices_by_lang = dict([(l['code'], l['voice']) for l in LANGUAGES.values()])
    if language not in voices_by_lang:
        raise Exception("Error: language should be in {}".format(', '.join(voices_by_lang.keys())))
    # POST 1
    data = {"name": name,
            "domains": [],
            "locale": language,
            "sources": []}
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    result = requests.post("https://developer.nuance.com/mix/nlu/api/v1/projects", data=json.dumps(data), cookies=cookies, headers=headers)
    if result.status_code  != 200:
        raise
    res_json = result.json()
    model_id = res_json.get("id")
    if model_id is None:
        raise
    #{"id": 6967, "name": "MODELNAME", "created": "2017-07-28T22:27:03.253884Z", "builds": [], "collaborators": [{"id": 6344, "name": "Thibault Cohen", "first_name": "Thibault", "last_name": "Cohen", "email": "titilambert@gmail.com", "telephone_num": null, "created_at": "2017-07-27T20:00:04.140590Z", "last_logged_in": "2017-07-28T20:54:20.902053Z", "thumbnail_url": "//www.gravatar.com/avatar/1e569dd79391d30b362b399c2629ac6e?d=https%3A%2F%2Fdeveloper.nuance.com%2Fmix%2Fnlu%2Fimages%2Fdefault_avatar_1.png&s=150", "lang": "en", "is_super_admin": false, "companies": []}], "owners": [6344], "domains": [], "notes": null, "languageDomainTopic": "nma", "locale": "en_US", "stats": {"ontology": {"nbPatterns": 0, "nbOntologyIntents": 1, "nbOntologyMentions": 18}, "nlu": {"verified": 0, "size": 0}}}
    # POST 2
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
        raise 
    # PUT 3
    url_put_3 = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(model_id)
    result = requests.put(url_put_3, cookies=cookies)


@nuance_login("mix")
def _list_models(username=None, password=None, cookies_file=None):
    result = requests.get("https://developer.nuance.com/mix/nlu/api/v1/projects", cookies=cookies)
    return result.json().get("data", [])

def list_models(username=None, password=None, cookies_file=None):
    """get model list from mix"""
    models = _list_models(username, password, cookies_file)
    if len(models) == 0:
        print("No model")
    else:
        for model in models:
            # {'name': 'coffeeMaker', 'type': {}, 'stats': {'ontology': {'nbOntologyIntents': 2, 'nbOntologyMentions': 20, 'nbPatterns': 24}, 'nlu': {'verified': 37, 'size': 37}}, 'metadata': {'source': ['Nuance Communications'], 'type': ['sample'], 'version': ['2.0.0'], 'description': ['Sample model for demonstration of 1 simple intent and two concepts'], 'created_by': ['titilambert@gmail.com', 'Thibault Cohen'], 'short_name': ['Coffee Maker Sample Model'], 'last_saved': ['Fri Jul 28 23:37:37 UTC 2017'], 'created_at': ['2017-07-28 20:55:09+00:00']}, 'locale': 'en_US', 'loaded': False, 'languageDomainTopic': 'nma', 'ontology': {'version': '', 'isLoaded': False}, 'sources': [{'name': 'nuance_custom_data', 'version': '1.0', 'displayName': 'nuance_custom_data', 'type': 'CUSTOM'}], 'created': '2017-07-28T20:55:10.156244Z', 'id': 6965}
            print("{id:6d} - {name:30s} - {locale} - {created}".format(**model))


def get_model_id(name, username=None, password=None, cookies_file=None):
    models = _list_models(username, password, cookies_file)

    model_id = None
    for model in models:
        if model.get("name") == name:
            model_id = model.get("id")
            break
        try:
            if model.get("id") == int(name):
                model_id = int(name)
                break
        except ValueError:
            pass
    if model_id is None:
        raise Exception("Project not found")

    return model_id


@nuance_login("mix")
def delete_model(name, username=None, password=None, cookies_file=None):
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
def model_train(name, username=None, password=None, cookies_file=None):
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


@nuance_login("mix")
def model_version(name, notes="", username=None, password=None, cookies_file=None):
    print("Versionning: {}".format(name))
    # Get model ID
    model_id = get_model_id(name, username, password, cookies_file)
    # Send Request
    url = "https://developer.nuance.com/mix/nlu/api/v1/nlu/{}/engine".format(model_id)
    params = {"notes": notes, "type": "Default", "with_asr": "true"}
    requests.post(url, params=params, cookies=cookies)
    # TODO check build status each second to wait completion


@nuance_login("mix")
def model_version_list(name, username=None, password=None, cookies_file=None):
    # Get model
    model = get_model(name, username, password, cookies_file)

    header = " Version | Status               | Created at          | Notes"
    print(header)
    for build in model.get("builds", []):
        build["created_at"] = build["created_at"][:19]
        line = "{version:8d} | {build_status:20s} | {created_at} | {notes}".format(**build)
        print(line)

@nuance_login("mix")
def model_attach(name, build_version=None, context_tag="latest", username=None, password=None, cookies_file=None):
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
        raise Exception("Can not get nmaid")
    nmaid = nmaids[0]
    # Attach
    print("attaching: {}".format(name))
    data = {"nmaid": nmaid,
            "project_id": model_id, "tag": context_tag}
    url = "https://developer.nuance.com/mix/nlu/bolt/applications/{}/configurations".format(app_id)
    result = requests.post(url, data=json.dumps(data), cookies=cookies, headers=headers)
    conf_id = result.json().get("id")
    if conf_id is None:
        raise

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
    result = requests.put(url, data=json.dumps(data), cookies=cookies, headers=headers)

