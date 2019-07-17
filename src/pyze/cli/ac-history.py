from .common import add_history_args, add_vehicle_args, get_vehicle
from datetime import datetime
from tabulate import tabulate


help_text = 'Show preconditioning history for your vehicle.'


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
            v.hvac_history(from_date, to_date),
            headers={
                'hvacSessionRequestDate': 'Request made',
                'hvacSessionStartDate': 'Start time',
                'hvacSessionEndStatus': 'Status'
            }
        )
    )
