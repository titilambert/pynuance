import json

from pynuance.libs.error import PyNuanceError


CODECS = ('wav', 'speex', 'opus')


def parse_credentials(file_path):

    with open(file_path) as f_creds:
        cred_json = json.load(f_creds)
        for attr in ("appId", "appKey"):
            if attr not in cred_json.keys():
                raise PyNuanceError("Missing {} in credentials file".format(attr))

        return cred_json["appId"], cred_json["appKey"], cred_json.get("context_tag")
