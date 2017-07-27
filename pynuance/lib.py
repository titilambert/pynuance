import json


     
Accept = {
    'mp3': {
        'mimetype': 'audio/mpeg' # bit rate: 128kbps
    },
    'wav': {
        'mimetype': 'audio/x-wav',
        'codec': 'pcm',
        'bit': 16,
        'rate': [8000,16000,22000]
    },
    'speex': {
        'mimetype': 'audio/x-speex',
        'rate': [8000,16000]
    },
    'amr': {
        'mimetype': 'audio/amr'
    }
}

CODECS = ('wav', 'speex', 'opus')


class PyNuanceError(Exception):
    pass


def parse_credentials(file_path):

    with open(file_path) as f_creds:
        cred_json = json.load(f_creds)
        for attr in ("appId", "appKey"):
            if attr not in cred_json.keys():
                raise PyNuanceError("Missing {} in credentials file".format(attr))

        return cred_json["appId"], cred_json["appKey"]
