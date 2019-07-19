from datetime import timedelta
from pyze.api import Kamereon, Vehicle

import dateparser


def add_vehicle_args(parser):
    parser.add_argument('-v', '--vin', help='VIN to use (defaults to first vehicle if not given)')
    parser.add_argument('-r', '--reg', help='Registration plate to use (defaults to first vehicle if not given)')


def add_history_args(parser):
    parser.add_argument('--from', dest='from_date', type=parse_date, help='Date to start showing history from')
    parser.add_argument('--to', type=parse_date, help='Date to finish showing history at (cannot be in the future)')


def parse_date(raw_date):
    return dateparser.parse(raw_date)


def get_vehicle(parsed_args):
    k = Kamereon()

    vehicles = k.get_vehicles().get('vehicleLinks')
    if parsed_args.vin:
        possible_vehicles = [v for v in vehicles if v['vin'] == parsed_args.vin]
        if len(possible_vehicles) == 0:
            raise RuntimeError('Specified VIN {} not found! Use `pyze vehicles` to list available vehicles.'.format(parsed_args.vin))

        vin = possible_vehicles[0]['vin']

    elif parsed_args.reg:
        possible_vehicles = [v for v in vehicles if v['vehicleDetails']['registrationNumber'] == parsed_args.vin.replace(' ', '').upper()][0]

        if len(possible_vehicles) == 0:
            raise RuntimeError('Specified registration plate {} not found! Use `pyze vehicles` to list available vehicles.'.format(parsed_args.reg))

        vin = possible_vehicles[0]['vin']

    else:
        vin = vehicles[0]['vin']

    return Vehicle(vin, k)


def format_duration_minutes(mins):
    d = timedelta(minutes=mins)
    return str(d)
