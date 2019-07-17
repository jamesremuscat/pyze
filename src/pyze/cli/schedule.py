from .common import add_vehicle_args, get_vehicle
from pyze.api.schedule import DAYS, ScheduledCharge
from tabulate import tabulate

import argparse
import re


def _parse_args(args):
    parser = argparse.ArgumentParser()

    add_vehicle_args(parser)

    subparsers = parser.add_subparsers()

    show_parser = subparsers.add_parser("show")
    show_parser.set_defaults(func=show)

    edit_parser = subparsers.add_parser("edit")
    edit_parser.set_defaults(func=edit)

    for day in DAYS:
        edit_parser.add_argument(
            '--{}'.format(day)
        )

    return parser.parse_args(args)


def run(args):
    parsed_args = _parse_args(args)

    v = get_vehicle(parsed_args)

    schedule = v.charge_schedule()

    if hasattr(parsed_args, 'func'):
        parsed_args.func(schedule, v, parsed_args)
    else:
        show(schedule, v, parsed_args)


def show(schedule, _, __):
    print_schedule(schedule)


def edit(schedule, vehicle, parsed_args):
    for day in DAYS:
        if hasattr(parsed_args, day):
            day_value = getattr(parsed_args, day)

            if day_value:
                start_time, duration = parse_day_value(day_value)
                schedule[day] = ScheduledCharge(start_time, duration)

    print('Setting new schedule:')
    print_schedule(schedule)
    vehicle.set_charge_schedule(schedule)
    print('It may take some time before these changes are reflected in your vehicle.')


def print_schedule(s):
    print(
        tabulate(
            format_schedule(s),
            headers=['Day', 'Start time', 'End time', 'Duration']
        )
    )


def format_schedule(s):
    return [
        [k.title(), *format_scheduled_charge(vs[0])] for k, vs in s.items()
    ]


def format_scheduled_charge(sc):
    return [
        format_stringy_time(sc.start_time),
        "{}{}".format(
            format_stringy_time(sc.finish_time),
            '+' if sc.spans_midnight else ''
        ),
        sc.duration
    ]


def format_stringy_time(raw):
    return "{}:{}".format(raw[0:2], raw[2:])


DAY_VALUE_REGEX = re.compile('(?P<start_time>[0-2][0-9][0-5][05]),(?P<duration>[0-9]+[05])')


def parse_day_value(raw):
    match = DAY_VALUE_REGEX.match(raw)
    if not match:
        raise RuntimeError('Invalid specification for charge schedule: `{}`'.format(raw))

    return [match.group('start_time'), int(match.group('duration'))]
