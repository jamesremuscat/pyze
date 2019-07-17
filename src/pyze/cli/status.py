from .common import add_vehicle_args, get_vehicle
from tabulate import tabulate

import argparse
import dateutil.parser
import dateutil.tz


KM_PER_MILE = 1.609344


def _parse_args(args):
    parser = argparse.ArgumentParser()
    add_vehicle_args(parser)
    parser.add_argument('--km', help='Give estimated range in kilometers (default is miles)', action='store_true')
    return parser.parse_args(args)


def run(args):
    parsed_args = _parse_args(args)
    v = get_vehicle(parsed_args)

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
