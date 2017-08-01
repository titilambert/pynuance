import os
import sys

import pytest

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
        self.context_tag = "ci-tag"

    @pytest.mark.order1
    def test_get_credentials(self):
        # Prepare command
        sys.argv = ["pynuance", 'credentials',
                    '-C', self.cookies_file,
                    '-c', self.credentials_file,
                    ]
        # Run it
        main()
        # Check it
        assert os.path.isfile(self.credentials_file)

    @pytest.mark.order2
    def test_mix_check(self, capsys):
        global MIX_READY
        # Prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'check',
                    ]
        # Run it
        main()
        out, err = capsys.readouterr()
        if out == "Your Mix account is activated, you can use NLU\n":
            # Mix ready
            assert True
            MIX_READY = True
        else:
            # Mix not ready
            assert out == "Your Mix account is being created or is not requested\n"
            MIX_READY = False

    @pytest.mark.order3
    def test_mix_model_create(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # Prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', '-m', self.model_name,
                    'create', '-l', 'en_US',
                    ]
        # Run it
        main()
        out, err = capsys.readouterr()
        # Check it
        assert out.startswith("""Model "{}" created with ID: """.format(self.model_name))

    @pytest.mark.order4
    def test_mix_model_list(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # Prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', 'list',
                    ]
        # Run it
        main()
        out, err = capsys.readouterr()
        # Check it
        #ssert out.startswith("""Model "{}" created with ID: """.format(self.model_name))
        assert out.find(" | {}".format(self.model_name)) != -1

    @pytest.mark.order5
    def test_mix_model_upload(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', '-m', self.model_name,
                    'upload', '-M', 'tests/upload.trsx'
                    ]
        # run it
        main()
        out, err = capsys.readouterr()
        # check it 
        assert out == ('''Sending: {}\nFile "{}" uploaded to model '''
                       '''"{}"\n'''.format(self.model_file, self.model_file, self.model_name))

    @pytest.mark.order6
    def test_mix_model_train(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', '-m', self.model_name,
                    'train',
                    ]
        # run it
        main()
        out, err = capsys.readouterr()
        # check it 
        assert out == ('''Training: {}\nModel "{}" trained\n'''.format(self.model_name,
                                                                       self.model_name))

    @pytest.mark.order7
    def test_mix_model_build_create(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', '-m', self.model_name,
                    'build', 'create',
                    ]
        # run it
        main()
        out, err = capsys.readouterr()
        # check it 
        assert out == ('New build created for model "{}"\n'.format(self.model_name))

    @pytest.mark.order8
    def test_mix_model_build_list(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', '-m', self.model_name,
                    'build', 'list',
                    ]
        # run it
        main()
        out, err = capsys.readouterr()
        # check it 
        assert out.find("1 | STARTED") != -1

    @pytest.mark.order9
    def test_mix_model_build_attach(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', '-m', self.model_name,
                    'build', 'attach', '-T', self.context_tag
                    ]
        # run it
        main()
        out, err = capsys.readouterr()
        # check it 
        assert out == ('The latest build of model "{}" is now attached to the "SandBox" App '
                       'with context tag "{}"\n'.format(self.model_name, self.context_tag))

    @pytest.mark.order10
    def test_mix_model_delete(self, capsys):
        # Test Mix account
        if not MIX_READY:
            pytest.skip("Mix account not ready")
        # Prepare command
        sys.argv = ["pynuance", 'mix',
                    '-C', self.cookies_file,
                    'model', '-m', self.model_name,
                    'delete',
                    ]
        # Run it
        main()
        out, err = capsys.readouterr()
        # Check it
        assert out == """Model "{}" deleted\n""".format(self.model_name)
