from pyze.api import Kamereon, Vehicle
from .common import add_vehicle_args, get_vehicle

import dateparser


help_text = 'Begin charging immediately (if your vehicle is plugged in).'


def configure_parser(parser):
    add_vehicle_args(parser)


def run(parsed_args):
    v = get_vehicle(parsed_args)
    v.charge_start()
