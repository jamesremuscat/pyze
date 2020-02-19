from .common import add_vehicle_args, format_duration_minutes, get_vehicle
from datetime import datetime
from pyze.api.schedule import DAYS, ScheduledCharge
from tabulate import tabulate
from tzlocal import get_localzone

import re


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

    for day in DAYS:
        if hasattr(parsed_args, day):
            day_value = getattr(parsed_args, day)

            if day_value:
                start_time, duration = parse_day_value(day_value)

                if not parsed_args.utc:
                    start_time = remove_offset(start_time)

                schedule[day] = ScheduledCharge(start_time, duration)

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


def timezone_offset():
    offset = get_localzone().utcoffset(datetime.now()).total_seconds() / 60
    return offset / 60, offset % 60


def apply_offset(raw):
    offset_hours, offset_minutes = timezone_offset()
    raw_hours = int(raw[1:3])
    raw_minutes = int(raw[4:6])

    return "{:02g}{:02g}".format(
        (raw_hours + offset_hours) % 24,
        raw_minutes + offset_minutes
    )


def remove_offset(raw):
    offset_hours, offset_minutes = timezone_offset()
    raw_hours = int(raw[1:3])
    raw_minutes = int(raw[4:6])

    return "T{:02g}:{:02g}Z".format(
        raw_hours - offset_hours,
        raw_minutes - offset_minutes
    )


DAY_VALUE_REGEX = re.compile('(?P<start_time>[0-2][0-9][0-5][05]),(?P<duration>[0-9]+[05])')


def parse_day_value(raw):
    match = DAY_VALUE_REGEX.match(raw)
    if not match:
        raise RuntimeError('Invalid specification for charge schedule: `{}`. Should be of the form HHMM,DURATION'.format(raw))

    start_time = match.group('start_time')
    formatted_start_time = 'T{}:{}Z'.format(
        start_time[:2],
        start_time[2:]
    )
    return [formatted_start_time, int(match.group('duration'))]
