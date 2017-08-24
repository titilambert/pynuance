"""CLI functions wrapper PyNuance functions"""

import json
import sys

import click

from pynuance import credentials as credentials_
from pynuance import mix
from pynuance import nlu
from pynuance import tts
from pynuance import stt
from pynuance.libs.languages import LANGUAGES
from pynuance.libs.error import PyNuanceError


#################################
# Validator functions
#################################
def _validate_voice(ctx, param, value):  # pylint: disable=W0613
    """Validate voice arguments"""
    language = ctx.params.get('language')
    voices_by_lang = dict([(l['code'], l['voice']) for l in LANGUAGES.values()])
    if value not in voices_by_lang[language]:
        raise click.BadParameter("Voice should be in "
                                 "{}".format(', '.join(voices_by_lang[language])))
    return value


def _validate_credentials_file(ctx, param, value):  # pylint: disable=W0613
    """Validate crendentials file"""
    with open(value) as f_creds:
        cred_json = json.load(f_creds)
        for attr in ("appId", "appKey"):
            if attr not in cred_json.keys():
                raise click.BadParameter("Missing {} in credentials file".format(attr))
    return {"appId": cred_json["appId"],
            "appKey": cred_json["appKey"],
            "context_tag": cred_json.get("context_tag"),
            }


#################################
# Cookies
#################################
@click.command()
@click.option('--username', '-U', required=True, help="Username")
@click.option('--password', '-P', required=True, help="Password")
@click.option('--cookies-file', '-C', required=True, help="Cookies file",
              type=click.Path(file_okay=True, dir_okay=False, writable=True))
def cookies(cookies_file, username=None, password=None):
    """CLI function to save cookie on the disk."""
    credentials_.save_cookies(cookies_file, username, password)
    click.echo("Cookies saved in file {}".format(cookies_file))


#################################
# Credentials
#################################
@click.command()
@click.option('--username', '-U', help="Username")
@click.option('--password', '-P', help="Password")
@click.option('--cookies-file', '-C', help="Cookies file",
              type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--credentials-file', '-c', help="Credentials file",
              type=click.Path(file_okay=True, dir_okay=False, writable=True))
def credentials(username=None, password=None, cookies_file=None, credentials_file=None):
    """Get App Id and App key from Nuance web site.

    Then show it or saved it in a file.
    """
    creds = credentials_.get_credentials(username, password, cookies_file)
    if credentials_file is None:
        click.echo("App Id:  {}".format(creds["appId"]))
        click.echo("App Key: {}".format(creds["appKey"]))
    else:
        # Save credentials in a file
        with open(credentials_file, "w") as fhc:
            json.dump(creds, fhc)
        click.echo("Credentials saved in file {}".format(credentials_file))


#################################
# Mix
#################################
@click.group("mix")
@click.option('--username', '-U', help="Username")
@click.option('--password', '-P', help="Password")
@click.option('--cookies-file', '-C', help="Cookies file",
              type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.pass_context
def cli_mix(ctx, username=None, password=None, cookies_file=None):
    """Entrypoint function for cli"""
    ctx.obj = {}
    ctx.obj['username'] = username
    ctx.obj['password'] = password
    ctx.obj['cookies_file'] = cookies_file


# Mix check
############
@click.command("check")
@click.pass_context
def mix_check(ctx):
    """Check if the account has access to Nuance Mix.

    URL: https://developer.nuance.com/mix/nlu/#/models/
    """
    result = mix.mix_activated(ctx.obj['username'], ctx.obj['password'], ctx.obj['cookies_file'])
    if result:
        click.echo("Your Mix account is activated, you can use NLU")
    else:
        click.echo("Your Mix account is being created or is not requested")


# Mix model
############
@click.group("model")
@click.pass_context
def mix_model(ctx):  # pylint: disable=W0613
    """Model subcommand"""


@click.command("list")
@click.pass_context
def mix_list_models(ctx):
    """Print all created models from Nuance Mix."""
    models = mix.list_models(ctx.obj['username'], ctx.obj['password'], ctx.obj['cookies_file'])
    if not models:
        click.echo("No model")
    else:
        header = " ID    | MODEL NAME                     | LANGUAGE   | CREATED AT"
        click.echo(header)
        for model in models:
            click.echo("{id:6d} | {name:30s} | {locale:10s} | {created}".format(**model))


@click.command("create")
@click.option('--name', '-n', required=True, help="Model name")
@click.option('--language', '-l', required=True, help="Language",
              type=click.Choice([l['code'] for l in LANGUAGES.values()]))
@click.pass_context
def mix_create_model(ctx, name, language):
    """Create a new model and print the result."""
    try:
        model = mix.create_model(name, language, ctx.obj['username'],
                                 ctx.obj['password'], ctx.obj['cookies_file'])
    except PyNuanceError as exp:
        click.echo("Error creating Mix model: {}".format(exp))
        sys.exit(1)
    click.echo('Model "{}" created with ID: {}'.format(name, model.get("id")))


@click.command("delete")
@click.option('--name', '-n', required=True, help="Model name")
@click.pass_context
def mix_delete_model(ctx, name):
    """Delete a model and print the result."""
    try:
        mix.delete_model(name, ctx.obj['username'], ctx.obj['password'], ctx.obj['cookies_file'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    click.echo('Model "{}" deleted'.format(name))


@click.command("upload")
@click.option('--name', '-n', required=True, help="Model name")
@click.option('--model-file', '-M', required=True, help="Model name", type=click.File())
@click.pass_context
def mix_upload_model(ctx, name, model_file):
    """Upload intent file into a Mix model and print the result."""
    try:
        mix.upload_model(name, model_file, ctx.obj['username'],
                         ctx.obj['password'], ctx.obj['cookies_file'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    click.echo('File "{}" uploaded to model "{}"'.format(model_file.name, name))


@click.command("train")
@click.option('--name', '-n', required=True, help="Model name")
@click.pass_context
def mix_train_model(ctx, name):
    """Train a mode and print the result."""
    try:
        mix.train_model(name, ctx.obj['username'], ctx.obj['password'], ctx.obj['cookies_file'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    click.echo('Model "{}" trained'.format(name))


# Mix build
#############
@click.group("build")
@click.option('--name', '-n', required=True, help="Model name")
@click.pass_context
def mix_model_build(ctx, name):
    """Entrypoint function for cli"""
    ctx.obj['name'] = name


@click.command("create")
@click.option('--notes', '-N', default="", help="Build notes")
@click.pass_context
def mix_model_build_create(ctx, notes):
    """Create a new model build and print the result."""
    try:
        mix.model_build_create(ctx.obj['name'], notes, ctx.obj['username'],
                               ctx.obj['password'], ctx.obj['cookies_file'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    click.echo('New build created for model "{}"'.format(ctx.obj['name']))


@click.command("list")
@click.pass_context
def mix_model_build_list(ctx):
    """List builds for a given model."""
    try:
        builds = mix.model_build_list(ctx.obj['name'], ctx.obj['username'],
                                      ctx.obj['password'], ctx.obj['cookies_file'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    if not builds:
        click.echo("No build for model {}".format(ctx.obj['name']))
    else:
        header = " Version | Status               | Created at          | Notes"
        click.echo(header)
        for build in builds:
            build["created_at"] = build["created_at"][:19]
            line = "{version:8d} | {build_status:20s} | {created_at} | {notes}".format(**build)
            click.echo(line)


@click.command("attach")
@click.option('--build-version', '-b', default=None, help="Build version")
@click.option('--context-tag', '-t', default="latest", help="Context tag")
@click.pass_context
def mix_model_build_attach(ctx, build_version=None, context_tag="latest"):
    """Attach a build to the Sandbox App and print result."""
    try:
        mix.model_build_attach(ctx.obj['name'], build_version, context_tag, ctx.obj['username'],
                               ctx.obj['password'], ctx.obj['cookies_file'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    if build_version is not None:
        click.echo('Build "{}" of model "{}" is now attached to the "SandBox" App '
                   'with context tag "{}"'.format(build_version, ctx.obj['name'], context_tag))
    else:
        click.echo('The latest build of model "{}" is now attached to the "SandBox" App '
                   'with context tag "{}"'.format(ctx.obj['name'], context_tag))


#################################
# NLU
#################################
@click.group("nlu")
@click.option('--context-tag', '-t', default="latest", help="Context tag")
@click.option('--credentials-file', '-c', required=True, help="Credentials file",
              callback=_validate_credentials_file,
              type=click.Path(file_okay=True, dir_okay=False, writable=True))
@click.option('--language', '-l', required=True, help="Language",
              type=click.Choice([l['code'] for l in LANGUAGES.values()]))
@click.pass_context
def cli_nlu(ctx, context_tag, credentials_file, language):
    """Entrypoint function for cli"""
    ctx.obj = {}
    ctx.obj['app_id'] = credentials_file["appId"]
    ctx.obj['app_key'] = credentials_file["appKey"]
    ctx.obj['context_tag'] = context_tag
    ctx.obj['language'] = language


@click.command("text")
@click.option('--text', '-T', required=True, help="Text")
@click.pass_context
def nlu_text(ctx, text):
    """Try to understand a text and print the result."""
    try:
        # TODO add support for user speaking
        result = nlu.understand_text(ctx.obj['app_id'], ctx.obj['app_key'],
                                     ctx.obj['context_tag'], text, ctx.obj['language'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    click.echo(json.dumps(result))


@click.command("audio")
@click.pass_context
def nlu_audio(ctx):
    """Try to understand audio from microphone and print the result."""
    try:
        result = nlu.understand_audio(ctx.obj['app_id'], ctx.obj['app_key'],
                                      ctx.obj['context_tag'], ctx.obj['language'])
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    click.echo(json.dumps(result))


#################################
# TTS
#################################
@click.command("tts")
@click.option('--credentials-file', '-c', required=True, help="Credentials file",
              callback=_validate_credentials_file,
              type=click.Path(file_okay=True, dir_okay=False, writable=True))
@click.option('--language', '-l', required=True, help="Language",
              type=click.Choice([l['code'] for l in LANGUAGES.values()]))
@click.option('--codec', '-d', required=True, help="codec",
              type=click.Choice(["speex", "opus", "l16"]))
@click.option('--voice', '-v', required=True, help="voice", callback=_validate_voice)
@click.option('--text', '-t', required=True, help="text")
def text_to_speech(credentials_file, language, voice, codec, text):
    """Read a text with a given language, voice and code and print result."""
    try:
        tts.text_to_speech(credentials_file["appId"], credentials_file["appKey"], language, voice, codec, text)
    except PyNuanceError as exp:
        click.echo("Error: {}".format(exp))
        sys.exit(1)
    click.echo('Text "{}" should be said'.format(text))


#################################
# STT
#################################
@click.command("stt")
@click.option('--credentials-file', '-c', required=True, help="Credentials file",
              callback=_validate_credentials_file,
              type=click.Path(file_okay=True, dir_okay=False, writable=True))
@click.option('--language', '-l', required=True, help="Language",
              type=click.Choice([l['code'] for l in LANGUAGES.values()]))
@click.option('--best-result/--all-result', '-a', default=False, help="Print all results")
@click.option('--raw', '-r', default=False, help="Print raw results in json format (imply --all)")
def speech_to_text(credentials_file, language, best_result=False, raw=False):
    """Speech to text from mic and print result."""
    try:
        result = stt.speech_to_text(credentials_file["appId"], credentials_file["appKey"], language)
    except PyNuanceError as exp:
        print("Error: {}".format(exp))
        sys.exit(1)
    if raw:
        click.echo(json.dumps(result))
    elif not result or not result.get("transcriptions"):
        click.echo("No result from Nuance. Check your microphone volume")
    else:
        if best_result:
            for transcription in result.get("transcriptions"):
                click.echo(transcription)
        else:
            click.echo(result.get("transcriptions")[0])


#################################
# Main cli
#################################
@click.group()
def cli_main():
    """Entrypoint function for cli"""
    pass


# Add cli command
cli_main.add_command(cookies)
cli_main.add_command(credentials)
cli_main.add_command(cli_mix)
# mix
cli_mix.add_command(mix_check)
# model
cli_mix.add_command(mix_model)
mix_model.add_command(mix_list_models)
mix_model.add_command(mix_create_model)
mix_model.add_command(mix_delete_model)
mix_model.add_command(mix_upload_model)
mix_model.add_command(mix_train_model)
mix_model.add_command(mix_model_build)
mix_model_build.add_command(mix_model_build_create)
mix_model_build.add_command(mix_model_build_list)
mix_model_build.add_command(mix_model_build_attach)
# nlu
cli_main.add_command(cli_nlu)
cli_nlu.add_command(nlu_text)
cli_nlu.add_command(nlu_audio)
# tts
cli_main.add_command(text_to_speech)
# stt
cli_main.add_command(speech_to_text)
