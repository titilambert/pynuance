import argparse
import sys

from pynuance.tts import tts
from pynuance.stt import stt
from pynuance.tools.credentials import get_credentials

from pynuance.lib import parse_credentials, PyNuanceError
from pynuance.languages import LANGUAGES


def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="command", help="Command", dest="command")
    # TTS
    parser_tts = subparsers.add_parser("tts", help="Text To Speech")
    parser_tts.add_argument('-c', '--credentials',
                            required=True, help='Credential file')
    parser_tts.add_argument('-l', '--language',
                            required=True, help='Language')
    parser_tts.add_argument('-v', '--voice',
                            required=True, help='Voice')
    parser_tts.add_argument('-C', '--codec',
                            required=True, help='Codec')
    parser_tts.add_argument('-t', '--text',
                            required=True, help='Text')
    # STT
    parser_stt = subparsers.add_parser("stt", help="Speech To Text")
    parser_stt.add_argument('-c', '--credentials',
                            required=True, help='Credential file')
    parser_stt.add_argument('-l', '--language',
                            required=True, help='Language')
    # Credentials
    parser_cred = subparsers.add_parser("credentials", help="Get Nuance Credentials")
    parser_cred.add_argument('-u', '--username',
                            help='Username')
    parser_cred.add_argument('-p', '--password',
                            help='Password')
    parser_cred.add_argument('-c', '--credential-file',
                            help='Credential file')

    args = parser.parse_args()


    if args.command == "credentials":
        # Run get credentials
        get_credentials(args.username, args.password, args.credential_file)

    else:
        creds = parse_credentials(args.credentials)

        # Check language
        voices_by_lang = dict([(l['code'], l['voice']) for l in LANGUAGES.values()])
        if args.language not in voices_by_lang:
            print("Error: language should be in {}".format(', '.join(voices_by_lang.keys())))
            sys.exit(1)

        # Handle command
        if args.command == "tts":
            # Check Voice
            if args.voice not in voices_by_lang[args.language]:
                print("Error: Voice should be in {}".format(', '.join(voices_by_lang[args.language])))
                sys.exit(2)
            # Run TTS command
            tts(creds[0], creds[1], args.language, args.voice, args.codec, args.text)

        elif args.command == "stt":
            # Run STT command
            stt(creds[0], creds[1], args.language)


   
if __name__ == '__main__':
    sys.exit(main())
