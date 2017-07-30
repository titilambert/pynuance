import argparse
import sys

from pynuance.tts import tts
from pynuance.stt import stt
from pynuance.credentials import get_credentials, save_cookies
from pynuance.mix import mix_available, create_model, delete_model, list_models, upload_model, model_train, model_version, model_version_list, model_attach
from pynuance.nlu import nlu_text

from pynuance.lib import parse_credentials, PyNuanceError
from pynuance.libs.languages import NLU_LANGUAGES


def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="command", help="Command", dest="command")
    # Cookies
    parser_cookies = subparsers.add_parser("cookies", help="Get Nuance Cookies")
    parser_cookies.add_argument('-u', '--username', help='Username')
    parser_cookies.add_argument('-p', '--password', help='Password')
    parser_cookies.add_argument('-C', '--cookies-file', help='Cookies file')
    # Credentials
    parser_cred = subparsers.add_parser("credentials", help="Get Nuance Credentials")
    parser_cred.add_argument('-u', '--username', help='Username')
    parser_cred.add_argument('-p', '--password', help='Password')
    parser_cred.add_argument('-c', '--credential-file', help='Credential file')
    parser_cred.add_argument('-C', '--cookies-file', help='Cookies file')
    # TTS
    parser_tts = subparsers.add_parser("tts", help="Text To Speech")
    parser_tts.add_argument('-c', '--credentials', required=True, help='Credential file')
    parser_tts.add_argument('-l', '--language', required=True, help='Language')
    parser_tts.add_argument('-v', '--voice', required=True, help='Voice')
    parser_tts.add_argument('-d', '--codec', required=True, help='Codec')
    parser_tts.add_argument('-t', '--text', required=True, help='Text')
    # STT
    parser_stt = subparsers.add_parser("stt", help="Speech To Text")
    parser_stt.add_argument('-c', '--credentials', required=True, help='Credential file')
    parser_stt.add_argument('-l', '--language', required=True, help='Language')
    # NLU
    parser_nlu = subparsers.add_parser("nlu", help="NLU - Natural Language Understanding")
    nlu_subparsers = parser_nlu.add_subparsers(title="NLU Commands", help="NLU Commands", dest="nlucommand")
    ## NLU Audio
    parser_nlu_audio = nlu_subparsers.add_parser("audio", help="NLU audio using mic")
    parser_nlu_audio.add_argument('-c', '--credentials', required=True, help='Credential file')
    parser_nlu_audio.add_argument('-l', '--language', required=True, help='Language')
    parser_nlu_audio.add_argument('-T', '--context_tag', required=True, help='Context tag')
    ## NLU Text
    parser_nlu_text = nlu_subparsers.add_parser("text", help="NLU text")
    parser_nlu_text.add_argument('-c', '--credentials', required=True, help='Credential file')
    parser_nlu_text.add_argument('-l', '--language', required=True, help='Language')
    parser_nlu_text.add_argument('-t', '--text', required=True, help='Text')
    parser_nlu_text.add_argument('-T', '--context_tag', required=True, help='Context tag')
    # MIX
    parser_mix = subparsers.add_parser("mix", help="Nuance Mix Command")
    mix_subparsers = parser_mix.add_subparsers(title="subcommand", help="SubCommand", dest="mixcommand")
    parser_mix.add_argument('-u', '--username', help='Username')
    parser_mix.add_argument('-p', '--password', help='Password')
    parser_mix.add_argument('-C', '--cookies-file', help='Cookies file')
    ## MIX Check
    parser_mix_check = mix_subparsers.add_parser("check", help="Check if mix is activated for your account")
    ## MIX Models
    parser_mixm = mix_subparsers.add_parser("model", help="Manage Mix models")
    mixm_subparsers = parser_mixm.add_subparsers(title="Mix model command", help="Mix Model Command", dest="mix_model_command")
    parser_mixm.add_argument('-m', '--model-name', help='Model name or ID')
    ## MIX Models list
    parser_mix_list = mixm_subparsers.add_parser("list", help="Check if mix is activated for your account")
    ## MIX Models create
    parser_mix_create = mixm_subparsers.add_parser("create", help="Check if mix is activated for your account")
    parser_mix_create.add_argument('-l', '--language', required=True, help='Language')
    ## MIX Models delete
    parser_mix_delete = mixm_subparsers.add_parser("delete", help="Check if mix is activated for your account")
    ## MIX Models upload (file)
    parser_mix_upload = mixm_subparsers.add_parser("upload", help="Upload model file")
    parser_mix_upload.add_argument('-M', '--model-file', required=True, help='Model file')
    ## MIX Models train
    parser_mix_train = mixm_subparsers.add_parser("train", help="Upload model file")
    ## MIX Models build
    parser_mixm_build = mixm_subparsers.add_parser("build", help="Manage Mix model buils")
    mixm_build_subparsers = parser_mixm_build.add_subparsers(title="Mix Model build command", help="Mix model build Command", dest="mix_model_build_command")
    ## MIX Models Build list
    parser_mixm_build_list = mixm_build_subparsers.add_parser("list", help="Upload model file")
    ## MIX Models Build create
    parser_mixm_build_create = mixm_build_subparsers.add_parser("create", help="Create a model build")
    parser_mixm_build_create.add_argument('-N', '--notes', default="", help='Version notes')
    ## MIX Models Build attach
    parser_mixm_build_attach = mixm_build_subparsers.add_parser("attach", help="Upload model file")
    parser_mixm_build_attach.add_argument('-b', '--build', default=None, help='Build')
    parser_mixm_build_attach.add_argument('-T', '--context-tag', default="latest", help='Context Tag')
    # Parse args
    args = parser.parse_args()



    if args.command == "cookies":
        # Run get credentials
        save_cookies(args.cookies_file, args.username, args.password)
    elif args.command == "credentials":
        # Run get credentials
        get_credentials(args.username, args.password, args.cookies_file, args.credential_file)
    elif args.command == "mix":
        # Mxi commands
        if args.mixcommand == "check":
            mix_available(args.username, args.password, args.cookies_file)
        elif args.mixcommand == "model":
            if args.mix_model_command == "list":
                list_models(args.username, args.password, args.cookies_file)
            else:
                if args.model_name is None:
                    print("ERROR: Missing model name\n")
                    parser_mixm.print_help()
                    sys.exit(1)
                if args.mix_model_command == "create":
                    create_model(args.model_name, args.language, args.username, args.password, args.cookies_file)
                elif args.mix_model_command == "delete":
                    delete_model(args.model_name, args.username, args.password, args.cookies_file)
                elif args.mix_model_command == "upload":
                    upload_model(args.model_name, args.model_file, args.username, args.password, args.cookies_file)
                elif args.mix_model_command == "train":
                    model_train(args.model_name, args.username, args.password, args.cookies_file)
                elif args.mix_model_command == "build":
                    if args.mix_model_build_command == "create":
                        model_version(args.model_name, args.notes, args.username, args.password, args.cookies_file)
                    elif args.mix_model_build_command == "list":
                        model_version_list(args.model_name, args.username, args.password, args.cookies_file)
                    elif args.mix_model_build_command == "attach":
                        model_attach(args.model_name, args.build, args.context_tag, args.username, args.password, args.cookies_file)
                    else:
                        parser_mixm_build.print_help()
                        sys.exit(1)
                else:
                    parser_mixm.print_help()
                    sys.exit(1)
        else:
            parser_mix.print_help()
            sys.exit(1)

    elif args.command == "nlu":
        creds = parse_credentials(args.credentials)
        # transform language
        # TODO put it in nlu_text func
        language = NLU_LANGUAGES.get(args.language)
        if language is None:
            print("Error: language not supported")
            sys.exit(1)
        # Run NLU TEXT command
        if args.context_tag is not None:
            context_tag = args.context_tag
        else:
            context_tag = creds[2]
        nlu_text(creds[0], creds[1], context_tag, language, args.text)

    elif args.command == "tts":
        # Check Voice
        # TODO put it in tts func
        if args.voice not in voices_by_lang[args.language]:
            print("Error: Voice should be in {}".format(', '.join(voices_by_lang[args.language])))
            sys.exit(1)
        # Run TTS command
        tts(creds[0], creds[1], args.language, args.voice, args.codec, args.text)

    elif args.command == "stt":
        # Run STT command
        stt(creds[0], creds[1], args.language)
    else:
        parser.print_help()
        sys.exit(1)

   
if __name__ == '__main__':
    sys.exit(main())
