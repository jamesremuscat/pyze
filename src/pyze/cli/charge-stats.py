from .common import add_history_args, add_vehicle_args, format_duration_minutes, get_vehicle
from datetime import datetime
from tabulate import tabulate


help_text = 'Show charging statistics for your vehicle.'


def configure_parser(parser):
    add_vehicle_args(parser)
    add_history_args(parser)
    parser.add_argument('--period', help='Period over which to aggregate', choices=['day', 'month'], default='month')


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
            [_format_charge_stat(s) for s in v.charge_statistics(from_date, to_date, parsed_args.period)],
            headers={
                'day': 'Day',
                'month': 'Month',
                'totalChargesNumber': 'Number of charges',
                'totalChargesDuration': 'Total time charging',
                'totalChargesErrors': 'Errors'
            }
        )
    )


def _format_charge_stat(s):
    s['totalChargesDuration'] = format_duration_minutes(s.get('totalChargesDuration', 0))
    return s
