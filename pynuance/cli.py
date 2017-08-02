"""CLI functions wrapper PyNuance functions"""

import json
import sys

from pynuance import credentials
from pynuance import mix
from pynuance import nlu
from pynuance import tts
from pynuance import stt
from pynuance.libs.error import PyNuanceError


def save_cookies(cookies_file, username=None, password=None):
    """CLI function to save cookie on the disk."""
    credentials.save_cookies(cookies_file, username, password)
    print("Cookies saved in file {}".format(cookies_file))


def get_credentials(username=None, password=None, cookies_file=None, credential_file=None):
    """Get App Id and App key from Nuance web site.

    Then show it or saved it in a file.
    """
    creds = credentials.get_credentials(username, password, cookies_file)
    if credential_file is None:
        print("App Id:  {}".format(creds["appId"]))
        print("App Key: {}".format(creds["appKey"]))
    else:
        # Save credentials in a file
        with open(credential_file, "w") as fhc:
            json.dump(creds, fhc)
        print("Credentials saved in file {}".format(credential_file))


def mix_activated(username=None, password=None, cookies_file=None):
    """Check if the account has access to Nuance Mix.

    URL: https://developer.nuance.com/mix/nlu/#/models/
    """
    result = mix.mix_activated(username, password, cookies_file)
    if result:
        print("Your Mix account is activated, you can use NLU")
    else:
        print("Your Mix account is being created or is not requested")


def list_models(username=None, password=None, cookies_file=None):
    """Print all created models from Nuance Mix."""
    models = mix.list_models(username, password, cookies_file)
    if not models:
        print("No model")
    else:
        header = " ID    | MODEL NAME                     | LANGUAGE   | CREATED AT"
        print(header)
        for model in models:
            print("{id:6d} | {name:30s} | {locale:10s} | {created}".format(**model))


def create_model(name, language, username=None, password=None, cookies_file=None):
    """Create a new model and print the result."""
    try:
        model = mix.create_model(name, language, username, password, cookies_file)
    except PyNuanceError as exp:
        print("Error creating Mix model: {}".format(exp))
        sys.exit(1)
    print('Model "{}" created with ID: {}'.format(name, model.get("id")))


def delete_model(name, username=None, password=None, cookies_file=None):
    """Delete a model and print the result."""
    try:
        mix.delete_model(name, username, password, cookies_file)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    print('Model "{}" deleted'.format(name))


def upload_model(name, model_file, username=None, password=None, cookies_file=None):
    """Upload intent file into a Mix model and print the result."""
    try:
        mix.upload_model(name, model_file, username, password, cookies_file)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    print('File "{}" uploaded to model "{}"'.format(model_file, name))


def train_model(name, username=None, password=None, cookies_file=None):
    """Train a mode and print the result."""
    try:
        mix.train_model(name, username, password, cookies_file)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    print('Model "{}" trained'.format(name))


def model_build_create(name, notes="", username=None, password=None, cookies_file=None):
    """Create a new model build and print the result."""
    try:
        mix.model_build_create(name, notes, username, password, cookies_file)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    print('New build created for model "{}"'.format(name))


def model_build_list(name, username=None, password=None, cookies_file=None):
    """List builds for a given model."""
    try:
        builds = mix.model_build_list(name, username, password, cookies_file)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    if not builds:
        print("No build for model {}".format(name))
    else:
        header = " Version | Status               | Created at          | Notes"
        print(header)
        for build in builds:
            build["created_at"] = build["created_at"][:19]
            line = "{version:8d} | {build_status:20s} | {created_at} | {notes}".format(**build)
            print(line)


def model_build_attach(name, build_version=None, context_tag="latest",
                       username=None, password=None, cookies_file=None):
    """Attach a build to the Sandbox App and print result."""
    try:
        mix.model_build_attach(name, build_version, context_tag, username, password, cookies_file)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    if build_version is not None:
        print('Build "{}" of model "{}" is now attached to the "SandBox" App '
              'with context tag "{}"'.format(build_version, name, context_tag))
    else:
        print('The latest build of model "{}" is now attached to the "SandBox" App '
              'with context tag "{}"'.format(name, context_tag))


def nlu_text(app_id, app_key, context_tag, language, text):
    """Try to understand a text and print the result."""
    try:
        result = nlu.understand_text(app_id, app_key, context_tag, language, text)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    print(json.dumps(result))


def nlu_audio(app_id, app_key, context_tag, language):
    """Try to understand audio from microphone and print the result."""
    try:
        result = nlu.understand_audio(app_id, app_key, context_tag, language)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    print(json.dumps(result))


def text_to_speech(app_id, app_key, lang, voice, codec, text):
    """Read a text with a given language, voice and code and print result."""
    try:
        tts.text_to_speech(app_id, app_key, lang, voice, codec, text)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    print('Text "{}" should be said'.format(text))


def speech_to_text(app_id, app_key, language, all_=False, raw=False):
    """Speech to text from mic and print result."""
    try:
        result = stt.speech_to_text(app_id, app_key, language)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    if raw:
        print(json.dumps(result))
    elif not result or not result[0].get("transcriptions"):
        print("No result from Nuance. Check your microphone volume")
    else:
        if all_:
            for transcription in result[0].get("transcriptions"):
                print(transcription)
        else:
            print(result[0].get("transcriptions")[0])
