from pyze.api import Kamereon, Vehicle
from .common import add_vehicle_args, get_vehicle

import dateparser


help_text = 'Activate your vehicle\'s preconditioning, now or in the future.'


def configure_parser(parser):
    add_vehicle_args(parser)
    parser.add_argument('--at', help='Date/time at which to complete preconditioning (defaults to immediate if not given). You can use times like "in 5 minutes" or "tomorrow at 9am".')
    parser.add_argument('-t', '--temperature', type=int, help='Target temperature (in Celsius)', default=21)
    parser.add_argument('--cancel', help='Cancel pending preconditioning', action='store_true')


def run(parsed_args):
    v = get_vehicle(parsed_args)

    if parsed_args.cancel:
        v.cancel_ac()
    else:
        if parsed_args.at:
            parsed_start_time = dateparser.parse(parsed_args.at)
        else:
            parsed_start_time = None

        v.ac_start(when=parsed_start_time, temperature=parsed_args.temperature)
