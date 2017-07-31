import os

from pynuance import cli


class TestUserHandling(object):

    def setup_method(self):
        self.username = os.environ.get("PYNUANCE_USERNAME")
        self.password = os.environ.get("PYNUANCE_PASSWORD")

    def test_save_cookies(self):
        cli.save_cookies("/tmp/test.json", self.username, self.password)
        assert os.path.isfile("/tmp/test.json")
