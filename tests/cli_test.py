import os

from pynuance import cli


class TestUserHandling(object):

    def setup_method(self):
        self.username = os.environ.get("PYNUANCE_USERNAME")
        self.password = os.environ.get("PYNUANCE_PASSWORD")
        self.cookies_file = os.environ.get("PYNUANCE_COOKIES")
        self.credentials_file = os.environ.get("PYNUANCE_CREDENTIALS")

    def test_get_credentials(self):
        cli.get_credentials(None, None, self.cookies_file, self.credentials_file)
        assert os.path.isfile("/tmp/test.json")
