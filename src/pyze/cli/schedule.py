from .common import add_vehicle_args, format_duration_minutes, get_vehicle
from datetime import datetime
from pyze.api.schedule import DAYS, ScheduledCharge, timezone_offset, apply_offset
from tabulate import tabulate


help_text = 'Show or edit your vehicle\'s charge schedule.'


def configure_parser(parser):
    add_vehicle_args(parser)

    parser.add_argument(
        '-u', '--utc',
        help='Treat all times as UTC and do no timezone conversion',
        action='store_true'
    )

    parser.add_argument(
        '--id',
        help='Schedule ID',
        type=int
    )

    subparsers = parser.add_subparsers()

    show_parser = subparsers.add_parser("show")
    show_parser.set_defaults(schedule_func=show)

    edit_parser = subparsers.add_parser("edit")
    edit_parser.set_defaults(schedule_func=edit)

    for day in DAYS:
        edit_parser.add_argument(
            '--{}'.format(day)
        )


def run(parsed_args):
    v = get_vehicle(parsed_args)

    schedules = v.charge_schedules()

    if hasattr(parsed_args, 'schedule_func'):
        parsed_args.schedule_func(schedules, v, parsed_args)
    else:
        show(schedules, v, parsed_args)


def show(schedules, _, parsed_args):
    for id, schedule in schedules.items():
        print('Schedule ID: {}{}'.format(id, ' [Active]' if schedule.activated else ''))
        print_schedule(schedule, parsed_args.utc)
    if parsed_args.utc:
        print('All times are UTC.')


def edit(schedules, vehicle, parsed_args):
    if parsed_args.id:
        schd_id = parsed_args.id
    else:
        schd_id = 1
    schedule = schedules[schd_id]
    schedules.update(schd_id, parsed_args)

    print('Setting new schedule (ID {}):'.format(schedule.id))
    print_schedule(schedule, parsed_args.utc)
    vehicle.set_charge_schedules(schedules)
    print('It may take some time before these changes are reflected in your vehicle.')


def print_schedule(s, use_utc):
    print(
        tabulate(
            format_schedule(s, use_utc),
            headers=['Day', 'Start time', 'End time', 'Duration']
        )
    )
    print()


def format_schedule(s, use_utc):
    return [
        [k.title(), *format_scheduled_charge(v, use_utc)] for k, v in s.items()
    ]


def format_scheduled_charge(sc, use_utc):

    if use_utc:
        start = sc.start_time
        finish = sc.finish_time
    else:
        start = apply_offset(sc.start_time)
        finish = apply_offset(sc.finish_time)

    offset = timezone_offset()
    offset_mins = offset[1] + (60 * offset[0])

    return [
        format_stringy_time(start),
        "{}{}".format(
            format_stringy_time(finish),
            '+' if sc.spans_midnight_in(offset_mins) else ''
        ),
        format_duration_minutes(sc.duration)
    ]


def format_stringy_time(raw):
    return "{}:{}".format(raw[0:2], raw[2:])
