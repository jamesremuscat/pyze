from pyze.api import Kamereon, Vehicle

import argparse
import dateutil.parser
import dateutil.tz


KM_PER_MILE = 1.609344


def _parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--vin', help='VIN to use (defaults to first vehicle if not given)')
    parser.add_argument('-r', '--reg', help='Registration plate to use (defaults to first vehicle if not given)')
    parser.add_argument('--km', help='Give estimated range in kilometers (default is miles)', action='store_true')
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

    status = v.battery_status()['data']['attributes']

    if parsed_args.km:
        range_text = '{:.1f} km'.format(status['rangeHvacOff'])
    else:
        range_text = '{:.1f} miles'.format(status['rangeHvacOff'] / KM_PER_MILE)

    print('Battery level: {}% ({})'.format(status['batteryLevel'], range_text))

    plugged_in, charging = status['plugStatus'] > 0, status['chargeStatus'] > 0

    print(
        '{} in, {}'.format(
            'Plugged' if plugged_in else 'Not plugged',
            'charging' if charging else 'not charging'
        )
    )

    print(
        'Updated at {}'.format(
            dateutil.parser.parse(
                status['lastUpdateTime']
            ).astimezone(
                dateutil.tz.tzlocal()
            ).strftime(
                '%Y-%m-%d %H:%M:%S'
            )
        )
    )
