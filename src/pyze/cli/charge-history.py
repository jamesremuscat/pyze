from .common import add_history_args, add_vehicle_args, format_duration_minutes, get_vehicle
from datetime import datetime
from tabulate import tabulate

import dateutil.parser
import dateutil.tz


help_text = 'Show charge history for your vehicle.'

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def configure_parser(parser):
    add_vehicle_args(parser)
    add_history_args(parser)


def run(parsed_args):
    v = get_vehicle(parsed_args)

    now = datetime.utcnow()

    if parsed_args.from_date:
        from_date = min(parsed_args.from_date, now)
    else:
        from_date = now.replace(day=1)

    if parsed_args.to:
        to_date = min(parsed_args.to, now)
    else:
        to_date = now

    print(
        tabulate(
            [_format_charge_history(h) for h in v.charge_history(from_date, to_date)],
            headers=[
                'Charge start',
                'Charge end',
                'Duration',
                'Power (kW)',
                'Started at (%)',
                'Charge gained (%)',
                'Power level',
                'Status'
            ]
        )
    )


def _format_charge_history(ch):

    if 'chargeStartDate' in ch:
        start_date = dateutil.parser.parse(
            ch['chargeStartDate']
        ).astimezone(
            dateutil.tz.tzlocal()
        ).strftime(DATE_FORMAT)
    else:
        start_date = ''

    if 'chargeEndDate' in ch:
        end_date = dateutil.parser.parse(
            ch['chargeEndDate']
        ).astimezone(
            dateutil.tz.tzlocal()
        ).strftime(DATE_FORMAT)
    else:
        end_date = ''

    if 'chargeDuration' in ch:
        chargeDuration = format_duration_minutes(ch['chargeDuration'])
    else:
        chargeDuration = ''

    # chargeStartInstantaneousPower seems to be missing for some charging sessions

    if 'chargeStartInstantaneousPower' in ch:
        chargeStartInstantaneousPower = '{:.2f}'.format(ch['chargeStartInstantaneousPower'] / 1000)
    else:
        chargeStartInstantaneousPower = ''

    if 'chargeBatteryLevelRecovered' in ch:
        chargeBatteryLevelRecovered = ch['chargeBatteryLevelRecovered']
    else:
        chargeBatteryLevelRecovered = ''

    return [
        start_date,
        end_date,
        chargeDuration,
        chargeStartInstantaneousPower,
        ch.get('chargeStartBatteryLevel'),
        chargeBatteryLevelRecovered,
        ch.get('chargePower'),
        ch.get('chargeEndStatus')
    ]
