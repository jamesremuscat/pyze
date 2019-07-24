from .common import add_vehicle_args, get_vehicle
from datetime import datetime
from pyze.api import ChargeMode


help_text = 'Set charge mode for your vehicle.'

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def configure_parser(parser):
    add_vehicle_args(parser)
    parser.add_argument('--always', help='Always charge when plugged in', action='store_true')
    parser.add_argument('--schedule', help='Charge according to schedule', action='store_true')


def run(parsed_args):
    if parsed_args.always == parsed_args.schedule:
        raise RuntimeError('Must specify either --always or --schedule')

    v = get_vehicle(parsed_args)

    if parsed_args.always:
        mode = ChargeMode.always_charging
    else:
        mode = ChargeMode.schedule_mode

    v.set_charge_mode(mode)
