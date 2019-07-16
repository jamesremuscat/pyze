from pyze.api import Kamereon, Vehicle
from tabulate import tabulate

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

    status = v.battery_status()
    # {'lastUpdateTime': '2019-07-12T00:38:01Z', 'chargePower': 2, 'instantaneousPower': 6600, 'plugStatus': 1, 'chargeStatus': 1, 'batteryLevel': 28, 'rangeHvacOff': 64, 'timeRequiredToFullSlow': 295}
    plugged_in, charging = status['plugStatus'] > 0, status['chargeStatus'] > 0
    charge_mode = v.charge_mode()['chargeMode']

    hvac = v.hvac_status()

    mileage = v.mileage()['totalMileage']

    if parsed_args.km:
        range_text = '{:.1f} km'.format(status['rangeHvacOff'])
        mileage_text = "{:.1f} km".format(mileage)
    else:
        range_text = '{:.1f} miles'.format(status['rangeHvacOff'] / KM_PER_MILE)
        mileage_text = "{:.1f} mi".format(mileage / KM_PER_MILE)

    if 'nextHvacStartDate' in hvac:
        hvac_start = dateutil.parser.parse(
            hvac['nextHvacStartDate']
        ).astimezone(
            dateutil.tz.tzlocal()
        ).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
    else:
        hvac_start = None

    update_time = dateutil.parser.parse(
        status['lastUpdateTime']
    ).astimezone(
        dateutil.tz.tzlocal()
    ).strftime(
        '%Y-%m-%d %H:%M:%S'
    )

    vehicle_table = [
        ["Battery level", "{}%".format(status['batteryLevel'])],
        ["Range estimate", range_text],
        ['Plugged in', 'Yes' if plugged_in else 'No'],
        ['Charging', 'Yes' if charging else 'No'],
        ['Charge rate', "{:.2f}kW".format(status['instantaneousPower'] / 1000)] if 'instantaneousPower' in status else None,
        ['Charge mode', charge_mode],
        ['AC state', hvac['hvacStatus']],
        ['AC start at', hvac_start] if hvac_start else None,
        ['External temperature', "{}°C".format(hvac['externalTemperature'])],
        ['Total mileage', mileage_text],
        ['Updated at', update_time]
    ]

    print(
        tabulate(
            [v for v in vehicle_table if v is not None]
        )
    )
