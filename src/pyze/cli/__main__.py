import argparse
import requests
import sys

from .ac import run as ac
from .login import run as login
from .status import run as status
from .vehicles import run as vehicles

commands = {
    'ac': ac,
    'login': login,
    'status': status,
    'vehicles': vehicles
}


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=commands.keys(), default='status', nargs='?')
    return parser


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    args, rest = argument_parser().parse_known_args(args)
    cmd = commands.get(args.command)

    try:
        cmd(rest)
    except requests.RequestException as e:
        print("Error communicating with Renault API!")
        print(e.response.text)


if __name__ == '__main__':
    main(sys.argv[1:])
