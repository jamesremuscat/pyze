from pyze.api import Kamereon, Vehicle

import argparse
import dateparser


def _parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--at', help='Date/time at which to complete preconditioning (defaults to immediate if not given). You can use times like "in 5 minutes" or "tomorrow at 9am".')
    parser.add_argument('-t', '--temperature', type=int, help='Target temperature (in Celsius)', default=21)
    parser.add_argument('-v', '--vin', help='VIN to use (defaults to first vehicle if not given)')
    parser.add_argument('-r', '--reg', help='Registration plate to use (defaults to first vehicle if not given)')
    return parser.parse_args(args)


def run(args):
    parsed_args = _parse_args(args)
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

    v = Vehicle(vin, k)

    if parsed_args.at:
        parsed_start_time = dateparser.parse(parsed_args.at)
    else:
        parsed_start_time = None

    result = v.ac_start(when=parsed_start_time, temperature=parsed_args.temperature)
