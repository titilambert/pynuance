import os
import sys
import time

import pytest
import click
from click.testing import CliRunner

from pynuance import cli
from pynuance.__main__ import main

MIX_READY = False

class TestUserHandling(object):

    def setup_method(self):
        self.username = os.environ.get("PYNUANCE_USERNAME")
        self.password = os.environ.get("PYNUANCE_PASSWORD")
        self.cookies_file = os.environ.get("PYNUANCE_COOKIES")
        self.credentials_file = os.environ.get("PYNUANCE_CREDENTIALS")
        self.model_name = "ci-model"
        self.model_file = "tests/upload.trsx"
        self.context_tag = "ci_tag"

    @classmethod
    def teardown_class(cls):
        cookies_file = os.environ.get("PYNUANCE_COOKIES")
        model_name = "ci-model"
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C', cookies_file,
                                              'model', 'delete',
                                              '-n', model_name])


    @pytest.mark.order1
    def test_get_credentials(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['credentials', '-C',self.cookies_file,
                    '-c', self.credentials_file ])
        assert result.exit_code == 0
        assert os.path.isfile(self.credentials_file)

    @pytest.mark.order2
    def test_mix_check(self):
        global MIX_READY
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file, 'check' ])
        if result.output == "Your Mix account is activated, you can use NLU\n":
            # Mix ready
            assert True
            MIX_READY = True
        else:
            # Mix not ready
            assert result.output == "Your Mix account is being created or is not requested\n"
            MIX_READY = False

    @pytest.mark.order3
    def test_mix_model_create(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # Prepare command
        runner = CliRunner()
        # Run it
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file,
                                              'model', 'create', '-n', self.model_name,
                                              '-l', 'en_US',])
        # Check it
        assert result.output.startswith("""Model "{}" created with ID: """.format(self.model_name))

    @pytest.mark.order4
    def test_mix_model_list(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # Prepare command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file, 'model', 'list' ])
        # Check it
        assert result.output.find(" | {}".format(self.model_name)) != -1

    @pytest.mark.order5
    def test_mix_model_upload(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # run it
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file, 'model', 'upload', '-n', self.model_name, '-M', 'tests/upload.trsx'])
        # check it 
        assert result.output == ('''Sending: {}\nFile "{}" uploaded to model '''
                                 '''"{}"\n'''.format(self.model_file,
                                                     self.model_file,
                                                     self.model_name))

    @pytest.mark.order6
    def test_mix_model_train(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # run command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file, 'model', 'train', '-n', self.model_name])
        # check it 
        assert result.output == ('''Training: {}\nModel "{}" trained\n'''.format(self.model_name,
                                                                                 self.model_name))
        # Wait for 5 sec for model training
        time.sleep(5)

    @pytest.mark.order7
    def test_mix_model_build_create(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # run command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file, 'model', 'build', '-n', self.model_name, 'create'])
        # check it 
        assert result.output == ('New build created for model "{}"\n'.format(self.model_name))
        # Wait for 5 sec for model build creation
        time.sleep(5)

    @pytest.mark.order8
    def test_mix_model_build_list(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # run command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file, 'model', 'build', '-n', self.model_name, 'list'])
        # check it 
        assert result.output.find(" 1 | ") != -1

    @pytest.mark.order9
    def test_mix_model_build_attach(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # prepare command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix', '-C',self.cookies_file, 'model', 'build', '-n', self.model_name, 'attach', '-t', self.context_tag])
        # check it 
        assert result.output == ('The latest build of model "{}" is now attached to the "SandBox" App '
                                 'with context tag "{}"\n'.format(self.model_name, self.context_tag))
        # Wait for 5 sec for model build attachment
        time.sleep(5)

    @pytest.mark.order10
    def test_mix_nlu_text(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # Prepare command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['nlu',
                    '-c', self.credentials_file,
                    '-l', 'en_US',
                    '-t', self.context_tag,
                    'text',
                    '-T', "What time is it ?",
                    ])
        # Check it
        assert result.output.find("get_time") != -1

    @pytest.mark.order11
    def test_mix_model_delete(self):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # Prepare command
        runner = CliRunner()
        result = runner.invoke(cli.cli_main, ['mix',
                    '-C', self.cookies_file,
                    'model',
                    'delete',
                     '-n', self.model_name,
                    ])
        # Check it
        assert result.output == """Model "{}" deleted\n""".format(self.model_name)
