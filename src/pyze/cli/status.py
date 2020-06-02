from .common import add_vehicle_args, format_duration_minutes, get_vehicle
from pyze.api import ChargeState, PlugState
from tabulate import tabulate

import collections
import dateutil.parser
import dateutil.tz
import requests


KM_PER_MILE = 1.609344

help_text = 'Show the current status of your vehicle.'


def configure_parser(parser):
    add_vehicle_args(parser)
    parser.add_argument('--km', help='Give distances in kilometers (default is miles)', action='store_true')
    parser.add_argument('--kw', help='Interpret charge rate as kilowatt (default is watt)', action='store_const', const=1, default=1000)


def wrap_unavailable(obj, method):
    wrapper = collections.defaultdict(lambda: 'Unavailable')

    try:
        original_dict = getattr(obj, method)()
        wrapper.update(original_dict)
    except requests.RequestException:
        wrapper['_unavailable'] = True

    return wrapper


def run(parsed_args):
    v = get_vehicle(parsed_args)

    status = wrap_unavailable(v, 'battery_status')
    # {'lastUpdateTime': '2019-07-12T00:38:01Z', 'chargePower': 2, 'instantaneousPower': 6600, 'plugStatus': 1, 'chargeStatus': 1, 'batteryLevel': 28, 'rangeHvacOff': 64, 'timeRequiredToFullSlow': 295}
    if status.get('_unavailable', False):
        plug_state = PlugState.NOT_AVAILABLE
        charge_state = ChargeState.NOT_AVAILABLE
        range_text = status['rangeHvacOff']
    else:
        try:
            plug_state = PlugState(status.get('plugStatus'))
        except ValueError:
            plug_state = PlugState.NOT_AVAILABLE

        try:
            charge_state = ChargeState(status.get('chargingStatus'))
        except ValueError:
            charge_state = ChargeState.NOT_AVAILABLE

        if 'batteryAutonomy' in status:
            if parsed_args.km:
                range_text = '{:.1f} km'.format(status['batteryAutonomy'])
            else:
                range_text = '{:.1f} miles'.format(status['batteryAutonomy'] / KM_PER_MILE)
        else:
            range_text = status['batteryAutonomy']  # Fall back to default value

    try:
        charge_mode = v.charge_mode()
    except requests.RequestException:
        charge_mode = 'Unavailable'

    mileage = wrap_unavailable(v, 'mileage')
    if mileage.get('_unavailable', False) or 'totalMileage' not in mileage:
        mileage_text = mileage['totalMileage']
    else:
        if parsed_args.km:
            mileage_text = "{:.1f} km".format(mileage['totalMileage'])
        else:
            mileage_text = "{:.1f} mi".format(mileage['totalMileage'] / KM_PER_MILE)

    location = wrap_unavailable(v, 'location')
    if location.get('_unavailable', False) or 'gpsLatitude' not in location:
        location_text = location['gpsLatitude']
    else:
        location_date = dateutil.parser.parse(
            location['lastUpdateTime']
        ).astimezone(
            dateutil.tz.tzlocal()
        ).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        location_text = "{:.8f},{:.8f} as of {}".format(location['gpsLatitude'], location['gpsLongitude'], location_date)

    hvac = wrap_unavailable(v, 'hvac_status')
    if hvac.get('_unavailable', False):
        hvac_start = hvac['nextHvacStartDate']
        external_temp = hvac['externalTemperature']
    elif 'nextHvacStartDate' in hvac:
        hvac_start = dateutil.parser.parse(
            hvac['nextHvacStartDate']
        ).astimezone(
            dateutil.tz.tzlocal()
        ).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        external_temp = "{}°C".format(hvac['externalTemperature'])
    else:
        hvac_start = None
        external_temp = "{}°C".format(hvac['externalTemperature'])

    try:
        update_time = dateutil.parser.parse(
            status['timestamp']
        ).astimezone(
            dateutil.tz.tzlocal()
        ).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
    except ValueError:
        update_time = status['timestamp']

    vehicle_table = [
        ["Battery level", "{}%".format(status['batteryLevel'])],
        ["Available energy", "{}kWh".format(status['batteryAvailableEnergy'])] if status.get('batteryAvailableEnergy', 0) > 0 else None,
        ["Range estimate", range_text],
        ['Plug state', plug_state.name],
        ['Charging state', charge_state.name],
        ['Charge rate', "{:.2f}kW".format(status['chargingInstantaneousPower'] / parsed_args.kw)] if 'chargingInstantaneousPower' in status else None,
        ['Time remaining', format_duration_minutes(status['chargingRemainingTime'])[:-3]] if 'chargingRemainingTime' in status else None,
        ['Charge mode', charge_mode.value if hasattr(charge_mode, 'value') else charge_mode],
        ['AC state', hvac['hvacStatus']] if 'hvacStatus' in hvac else None,
        ['AC start at', hvac_start] if hvac_start else None,
        ['External temperature', external_temp],
        ['Battery temperature', "{}°C".format(status['batteryTemperature'])] if 'batteryTemperature' in status else None,
        ['Total mileage', mileage_text],
        ['Updated at', update_time],
        ['Location', location_text]
    ]

    print(
        tabulate(
            [v for v in vehicle_table if v is not None]
        )
    )
