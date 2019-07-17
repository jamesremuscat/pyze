from pyze.api import Kamereon, Vehicle
from .common import add_vehicle_args, get_vehicle

import argparse
import dateparser


def _parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--at', help='Date/time at which to complete preconditioning (defaults to immediate if not given). You can use times like "in 5 minutes" or "tomorrow at 9am".')
    parser.add_argument('-t', '--temperature', type=int, help='Target temperature (in Celsius)', default=21)
    add_vehicle_args(parser)
    return parser.parse_args(args)


def run(args):
    parsed_args = _parse_args(args)
    v = get_vehicle(parsed_args)

    if parsed_args.at:
        parsed_start_time = dateparser.parse(parsed_args.at)
    else:
        parsed_start_time = None

    result = v.ac_start(when=parsed_start_time, temperature=parsed_args.temperature)
