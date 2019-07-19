from .common import add_history_args, add_vehicle_args, format_duration_minutes, get_vehicle
from datetime import datetime
from tabulate import tabulate


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
                'Charge gained (%)',
                'Status'
            ]
        )
    )


def _format_charge_history(ch):

    start_date = dateutil.parser.parse(
        ch['chargeStartDate']
    ).astimezone(
        dateutil.tz.tzlocal()
    )

    end_date = dateutil.parser.parse(
        ch['chargeEndDate']
    ).astimezone(
        dateutil.tz.tzlocal()
    )

    return [
        start_date.strftime(DATE_FORMAT),
        end_date.strftime(DATE_FORMAT),
        format_duration_minutes(ch['chargeDuration']),
        '{:.2f}'.format(ch['chargeStartInstantaneousPower'] / 1000),
        ch['chargeBatteryLevelRecovered'],
        ch['chargeEndStatus']
    ]
