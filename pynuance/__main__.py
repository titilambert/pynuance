"""Entrypoint for CLI"""
import sys

from pynuance.cli import cli_main


def main():
    """Main function"""
    cli_main()


if __name__ == '__main__':
    sys.exit(main())
