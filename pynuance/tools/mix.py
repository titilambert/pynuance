#!/usr/bin/env python

import json

import requests
from bs4 import BeautifulSoup

from pynuance.tools.nuance_dev_http_lib import dev_login, mix_login


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

def create_project(name, language, username=None, password=None):

    # login
    cookies = mix_login(username, password)
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
    project_id = res_json.get("id")
    if project_id is None:
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
    url_put_3 = "https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(project_id)
    result = requests.put(url_put_3, cookies=cookies)

def _list_projects(cookies=None):
#    result = requests.get("https://developer.nuance.com/mix/nlu/#/models/", cookies=cookies)
    result = requests.get("https://developer.nuance.com/mix/nlu/api/v1/projects", cookies=cookies)

    return result.json().get("data", [])

def list_projects(username, password):
    # login
    cookies = mix_login(username, password)
    
    projects = _list_projects(cookies)
    for project in projects:
        # {'name': 'coffeeMaker', 'type': {}, 'stats': {'ontology': {'nbOntologyIntents': 2, 'nbOntologyMentions': 20, 'nbPatterns': 24}, 'nlu': {'verified': 37, 'size': 37}}, 'metadata': {'source': ['Nuance Communications'], 'type': ['sample'], 'version': ['2.0.0'], 'description': ['Sample model for demonstration of 1 simple intent and two concepts'], 'created_by': ['titilambert@gmail.com', 'Thibault Cohen'], 'short_name': ['Coffee Maker Sample Model'], 'last_saved': ['Fri Jul 28 23:37:37 UTC 2017'], 'created_at': ['2017-07-28 20:55:09+00:00']}, 'locale': 'en_US', 'loaded': False, 'languageDomainTopic': 'nma', 'ontology': {'version': '', 'isLoaded': False}, 'sources': [{'name': 'nuance_custom_data', 'version': '1.0', 'displayName': 'nuance_custom_data', 'type': 'CUSTOM'}], 'created': '2017-07-28T20:55:10.156244Z', 'id': 6965}
        print("{id:6d} - {name:30s} - {locale} - {created}".format(**project))


def delete_project(name, username, password):
    # login
    cookies = mix_login(username, password)

    projects = _list_projects(cookies)

    project_id = None
    for project in projects:
        if project.get("name") == name:
            project_id = project.get("id")
            break
        try:
            if project.get("id") == int(name):
                project_id = int(name)
                break
        except ValueError:
            pass
    if project_id is None:
        raise Exception("Project not found")

    data = {"session_id": "-1",
            "project_id": "-1",
            "page":"/model/{}/dashboard".format(project_id),
            "query_params":{},
            "host":"developer.nuance.com",
            "port":"",
            "protocol":"https",
            "category":"model",
            "action":"delete",
            "label":"cancelled",
            "value": project_id}

    result = requests.post("https://developer.nuance.com/mix/nlu/bolt/ubt", data=json.dumps(data), cookies=cookies)
    
    if result.status_code != 200:
        raise

    result = requests.delete("https://developer.nuance.com/mix/nlu/api/v1/projects/{}".format(project_id), cookies=cookies)
    if result.status_code != 204:
        raise
