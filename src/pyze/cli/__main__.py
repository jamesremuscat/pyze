import argparse
import sys

from .login import run as login
from .vehicles import run as vehicles

commands = {
    'login': login,
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
    cmd(rest)


if __name__ == '__main__':
    main(sys.argv[1:])
