import argparse
import importlib
import requests
import sys

from .ac import run as ac
from .login import run as login
from .schedule import run as schedule
from .status import run as status
from .vehicles import run as vehicles

COMMAND_MODULES = [
    'ac',
    'ac-history',
    'ac-stats',
    'charge-history',
    'charge-mode',
    'charge-stats',
    'login',
    'schedule',
    'status',
    'vehicles'
]


def argument_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='subparser', metavar='COMMAND')

    for module_name in COMMAND_MODULES:
        module = importlib.import_module('.{}'.format(module_name), __package__)

        if hasattr(module, 'help_text'):
            help_text = module.help_text
        else:
            help_text = None

        subparser = subparsers.add_parser(module_name, description=help_text, help=help_text)

        if hasattr(module, 'configure_parser'):
            module.configure_parser(subparser)
        subparser.set_defaults(func=module.run)

    return parser


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    parser = argument_parser()

    parsed_args = parser.parse_args(args)

    if not parsed_args.subparser:
        parsed_args = parser.parse_args(args + ['status'])

    try:
        parsed_args.func(parsed_args)
    except requests.RequestException as e:
        print("Error communicating with Renault API!")
        print(e.response.text)


if __name__ == '__main__':
    main(sys.argv[1:])
