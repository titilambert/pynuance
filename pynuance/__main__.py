"""Entrypoint for CLI"""
import argparse
import sys

from pynuance import cli

from pynuance.libs.common import parse_credentials


def main():  # pylint: disable=R0912,R0915
    """Main function"""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="command", help="Command", dest="command")
    # Cookies
    parser_cookies = subparsers.add_parser("cookies", help="Get Nuance Cookies")
    parser_cookies.add_argument('-u', '--username', help='Username')
    parser_cookies.add_argument('-p', '--password', help='Password')
    parser_cookies.add_argument('-C', '--cookies-file', required=True, help='Cookies file')
    # *Credentials
    parser_cred = subparsers.add_parser("credentials", help="Get Nuance Credentials")
    parser_cred.add_argument('-u', '--username', help='Username')
    parser_cred.add_argument('-p', '--password', help='Password')
    parser_cred.add_argument('-c', '--credential-file', help='Credential file')
    parser_cred.add_argument('-C', '--cookies-file', help='Cookies file')
    # *TTS
    parser_tts = subparsers.add_parser("tts", help="Text To Speech")
    parser_tts.add_argument('-c', '--credentials', required=True, help='Credential file')
    parser_tts.add_argument('-l', '--language', required=True, help='Language')
    parser_tts.add_argument('-v', '--voice', required=True, help='Voice')
    parser_tts.add_argument('-d', '--codec', required=True, help='Codec')
    parser_tts.add_argument('-t', '--text', required=True, help='Text')
    # *STT
    parser_stt = subparsers.add_parser("stt", help="Speech To Text")
    parser_stt.add_argument('-c', '--credentials', required=True, help='Credential file')
    parser_stt.add_argument('-l', '--language', required=True, help='Language')
    parser_stt.add_argument('-a', '--all', default=False, action="store_true",
                            help='Print all results')
    parser_stt.add_argument('-r', '--raw', default=False, action="store_true",
                            help='Print raw results in json format (imply --all)')
    # *NLU
    parser_nlu = subparsers.add_parser("nlu", help="NLU - Natural Language Understanding")
    parser_nlu.add_argument('-c', '--credentials', required=True, help='Credential file')
    parser_nlu.add_argument('-l', '--language', required=True, help='Language')
    parser_nlu.add_argument('-T', '--context_tag', required=True, help='Context tag')
    nlu_subparsers = parser_nlu.add_subparsers(title="NLU Commands", help="NLU Commands",
                                               dest="nlucommand")
    # **NLU Audio
    nlu_subparsers.add_parser("audio", help="NLU audio using mic")
    # **NLU Text
    parser_nlu_text = nlu_subparsers.add_parser("text", help="NLU text")
    parser_nlu_text.add_argument('-t', '--text', required=True, help='Text')
    # *MIX
    parser_mix = subparsers.add_parser("mix", help="Nuance Mix Command")
    mix_subparsers = parser_mix.add_subparsers(title="subcommand", help="SubCommand",
                                               dest="mixcommand")
    parser_mix.add_argument('-u', '--username', help='Username')
    parser_mix.add_argument('-p', '--password', help='Password')
    parser_mix.add_argument('-C', '--cookies-file', help='Cookies file')
    # **MIX Check
    mix_subparsers.add_parser("check", help=("Check if mix is activated "
                                             "for your account"))
    # **MIX Models
    parser_mixm = mix_subparsers.add_parser("model", help="Manage Mix models")
    mixm_subparsers = parser_mixm.add_subparsers(title="Mix model command",
                                                 help="Mix Model Command",
                                                 dest="mix_model_command")
    parser_mixm.add_argument('-m', '--model-name', help='Model name or ID')
    # ***MIX Models list
    mixm_subparsers.add_parser("list", help=("Check if mix is activated "
                                             "for your account"))
    # ***MIX Models create
    parser_mix_create = mixm_subparsers.add_parser("create", help=("Check if mix is activated "
                                                                   "for your account"))
    parser_mix_create.add_argument('-l', '--language', required=True, help='Language')
    # ***MIX Models delete
    mixm_subparsers.add_parser("delete", help=("Check if mix is activated "
                                               "for your account"))
    # ***MIX Models upload (file)
    parser_mix_upload = mixm_subparsers.add_parser("upload", help="Upload model file")
    parser_mix_upload.add_argument('-M', '--model-file', required=True, help='Model file')
    # ***MIX Models train
    mixm_subparsers.add_parser("train", help="Upload model file")
    # ****MIX Models build
    parser_mixm_build = mixm_subparsers.add_parser("build", help="Manage Mix model buils")
    mixm_build_subparsers = parser_mixm_build.add_subparsers(title="Mix Model build command",
                                                             help="Mix model build Command",
                                                             dest="mix_model_build_command")
    # ****MIX Models Build list
    mixm_build_subparsers.add_parser("list", help="Upload model file")
    # ****MIX Models Build create
    parser_mixm_build_create = mixm_build_subparsers.add_parser("create",
                                                                help="Create a model build")
    parser_mixm_build_create.add_argument('-N', '--notes', default="", help='Version notes')
    # ****MIX Models Build attach
    parser_mixm_build_attach = mixm_build_subparsers.add_parser("attach",
                                                                help="Upload model file")
    parser_mixm_build_attach.add_argument('-b', '--build', default=None, help='Build')
    parser_mixm_build_attach.add_argument('-T', '--context-tag', default="latest",
                                          help='Context Tag')
    # Parse args
    args = parser.parse_args()

    # Running commands
    if args.command == "cookies":
        # Run get credentials
        cli.save_cookies(args.cookies_file, args.username, args.password)
    elif args.command == "credentials":
        # Run get credentials
        cli.get_credentials(args.username, args.password, args.cookies_file, args.credential_file)
    elif args.command == "mix":
        # Mix commands
        if args.mixcommand == "check":
            # Mix Check command
            cli.mix_activated(args.username, args.password, args.cookies_file)
        elif args.mixcommand == "model":
            # Mix model commands
            if args.mix_model_command == "list":
                cli.list_models(args.username, args.password, args.cookies_file)
            else:
                if args.model_name is None:
                    print("ERROR: Missing model name\n")
                    parser_mixm.print_help()
                    sys.exit(1)
                if args.mix_model_command == "create":
                    cli.create_model(args.model_name, args.language, args.username,
                                     args.password, args.cookies_file)
                elif args.mix_model_command == "delete":
                    cli.delete_model(args.model_name, args.username, args.password,
                                     args.cookies_file)
                elif args.mix_model_command == "upload":
                    cli.upload_model(args.model_name, args.model_file, args.username,
                                     args.password, args.cookies_file)
                elif args.mix_model_command == "train":
                    cli.train_model(args.model_name, args.username, args.password,
                                    args.cookies_file)
                elif args.mix_model_command == "build":
                    if args.mix_model_build_command == "create":
                        cli.model_build_create(args.model_name, args.notes, args.username,
                                               args.password, args.cookies_file)
                    elif args.mix_model_build_command == "list":
                        cli.model_build_list(args.model_name, args.username,
                                             args.password, args.cookies_file)
                    elif args.mix_model_build_command == "attach":
                        cli.model_build_attach(args.model_name, args.build, args.context_tag,
                                               args.username, args.password, args.cookies_file)
                    else:
                        # Print mix model build help
                        parser_mixm_build.print_help()
                        sys.exit(1)
                else:
                    # Print mix model help
                    parser_mixm.print_help()
                    sys.exit(1)
        else:
            # Print mix help
            parser_mix.print_help()
            sys.exit(1)

    elif args.command == "nlu":
        creds = parse_credentials(args.credentials)
        if args.context_tag is not None:
            context_tag = args.context_tag
        else:
            context_tag = creds[2]
        if args.nlucommand == "text":
            # Run NLU TEXT command
            cli.nlu_text(creds[0], creds[1], context_tag, args.language, args.text)
        elif args.nlucommand == "audio":
            # Run NLU TEXT command
            cli.nlu_audio(creds[0], creds[1], context_tag, args.language)

    elif args.command == "tts":
        creds = parse_credentials(args.credentials)
        # Run TTS command
        cli.text_to_speech(creds[0], creds[1], args.language, args.voice, args.codec, args.text)

    elif args.command == "stt":
        creds = parse_credentials(args.credentials)
        # Run STT command
        cli.speech_to_text(creds[0], creds[1], args.language, args.all, args.raw)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
