from enum import Enum
from tzlocal import get_localzone
from datetime import datetime

import math
import re


DAYS = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday'
]


def _parse_schedule(data):
    schedule = {}
    for day in DAYS:
        if day in data:
            schedule[day] = ScheduledCharge(
                data[day]['startTime'],
                data[day]['duration']
            )

    return data.get('id'), data.get('activated', False), schedule


MINUTES_IN_DAY = 60 * 24


class ChargeMode(Enum):
    always = 'Always'
    always_charging = 'Always charge'
    schedule_mode = 'Scheduled charge'


class ChargeSchedules(object):
    def __init__(self, raw={}):
        self._schedules = {}

        for schedule in raw.get('schedules', []):
            self._schedules[schedule['id']] = ChargeSchedule(schedule)

        self.mode = raw.get('mode', 'scheduled')

    def __getitem__(self, key):
        return self._schedules[key]

    def __setitem__(self, key, value):
        if not isinstance(value, ChargeSchedule):
            raise RuntimeError('Expected ChargeSchedule, got {} instead'.format(value.__class__))
        self._schedules[key] = value

    def _next_schedule_id(self):
        return max(list(self._schedules.keys()) + [0]) + 1

    def add(self, schedule):
        if not isinstance(schedule, ChargeSchedule):
            raise RuntimeError('Expected ChargeSchedule, got {} instead'.format(schedule.__class__))
        if not schedule.id:
            schedule.id = self._next_schedule_id()
        self._schedules[schedule.id] = schedule

    def new_schedule(self):
        schedule = ChargeSchedule()
        schedule.id = self._next_schedule_id()
        self._schedules[schedule.id] = schedule
        return schedule

    def items(self):
        return self._schedules.items()

    def __iter__(self):
        return self._schedules.items().__iter__()

    def __len__(self):
        return self._schedules.__len__()

    def for_json(self):
        return {
            'schedules': list(map(lambda v: v.for_json(), self._schedules.values()))
        }

    def validate(self):
        seen_active = False
        for schedule in self._schedules.values():
            schedule.validate()
            if schedule.activated:
                if seen_active:
                    raise InvalidScheduleException('Multiple schedules are active')
                seen_active = True
        return True

    def update(self, id, args):
        schedule = self._schedules[id]
        schedule.update(args)


INITIAL_SCHEDULE = {
    'activated': False
}

for day in DAYS:
    INITIAL_SCHEDULE[day] = {
        'startTime': 'T12:00Z',
        'duration': 15
    }


class ChargeSchedule(object):
    def __init__(self, data=INITIAL_SCHEDULE):
        self.id, self.activated, self._schedule = _parse_schedule(data)

    def update(self, args):
        for day in DAYS:
            if hasattr(args, day):
                day_value = getattr(args, day)

                if day_value:
                    start_time, duration = parse_day_value(day_value)

                    if not hasattr(args, 'utc'):
                        start_time = remove_offset(start_time)

                    self[day] = ScheduledCharge(start_time, duration)

    def validate(self):
        for day, charge_time in self._schedule.items():
            charge_time.validate()

            if charge_time.spans_midnight:
                next_day = DAYS[(DAYS.index(day) + 1) % len(DAYS)]
                tomorrow_charge = self._schedule.get(next_day)
                if tomorrow_charge and charge_time.overlaps(tomorrow_charge):
                    raise InvalidScheduleException('Charge for {} overlaps charge for {}'.format(day, next_day))
        return True

    def __getitem__(self, key):
        return self._schedule[key]

    def __setitem__(self, key, value):
        if key not in DAYS:
            raise RuntimeError('{} is not a valid day'.format(key))
        if not isinstance(value, ScheduledCharge):
            raise RuntimeError('Expected ScheduledCharge, got {} instead'.format(value.__class__))
        value.validate()

        # Note: we must allow the schedule to be invalidated here as it might require subsequent assignments
        # to make it valid (or else risk it being essentially immutable without gymnastics).
        self._schedule[key] = value

    def __delitem__(self, key):
        return self._schedule.__delitem__(key)

    def items(self):
        return self._schedule.items()

    def __iter__(self):
        return self._schedule.items().__iter__()

    def __repr__(self):
        return '<ChargeSchedule {}>'.format(self._schedule)

    def for_json(self):
        result = {
            'id': self.id,
            'activated': self.activated
        }
        for day, schedule in self._schedule.items():
            result[day] = schedule.for_json()
        return result


class ScheduledCharge(object):
    def __init__(self, start_time, duration):
        self.start_time = start_time
        self.duration = duration

    @staticmethod
    def between(start, end):
        '''
        Convenience method for creating a scheduled charge between two
        datetimes. The date part of the datetimes is used only for calculating
        the interval between them (hence the duration of the charge).

        Times should be in UTC. No timezone conversion is applied by this method.
        '''
        if not isinstance(start, datetime):
            raise RuntimeError('Expected start to be a datetime, got {} instead'.format(start.__class__))
        if not isinstance(end, datetime):
            raise RuntimeError('Expected end to be a datetime, got {} instead'.format(end.__class__))
        if start >= end:
            raise RuntimeError('Start time should be before end time.')

        start_rounded = round_date_fifteen(start)
        end_rounded = round_date_fifteen(end)

        start_string = 'T{:02g}:{:02g}Z'.format(
            start_rounded.hour,
            start_rounded.minute
        )

        duration = round_fifteen((end_rounded - start_rounded).total_seconds() // 60)

        if duration < 15:
            raise RuntimeError('Duration must be at least 15 minutes')

        return ScheduledCharge(start_string, duration)

    def validate(self):
        _validate_start_time(self.start_time)
        _validate_duration(self.duration)

    @property
    def spans_midnight(self):
        start = _minuteize(self.start_time)
        finish = start + self.duration
        return finish >= MINUTES_IN_DAY

    def spans_midnight_in(self, tzoffset):
        start = (_minuteize(self.start_time) + tzoffset) % MINUTES_IN_DAY
        finish = start + self.duration
        return finish >= MINUTES_IN_DAY

    @property
    def finish_time_minutes(self):
        start = _minuteize(self.start_time)
        finish = start + self.duration
        return finish % MINUTES_IN_DAY

    @property
    def finish_time(self):
        return _deminuteize(self.finish_time_minutes)

    def overlaps(self, other):
        return self.finish_time_minutes >= _minuteize(other.start_time)

    def __repr__(self):
        return '(Start {}, duration {})'.format(self.start_time, self.duration)

    def for_json(self):
        return {
            'startTime': self.start_time,
            'duration': self.duration
        }


class InvalidScheduleException(Exception):
    pass


def _validate_start_time(start_time):
    if isinstance(start_time, str):
        if len(start_time) == 7:
            if start_time[0] == 'T' and start_time[3] == ':' and start_time[6] == 'Z':
                hour = start_time[1:3]
                minute = start_time[4:6]

                if 0 <= int(hour) < 24:
                    if minute in ['00', '15', '30', '45']:
                        return True
    raise InvalidScheduleException("{} is not a valid start time".format(start_time))


def _validate_duration(duration):
    if isinstance(duration, int):
        if duration % 15 == 0:
            return duration >= 15
    raise InvalidScheduleException("{} is not a valid duration".format(duration))


def _minuteize(timestr):
    return (int(timestr[1:3]) * 60) + int(timestr[4:6])


def _deminuteize(tval):
    return 'T{:02g}:{:02g}Z'.format(
        math.floor(tval / 60),
        tval % 60
    )


def round_fifteen(val):
    return (val // 15) * 15


def round_date_fifteen(dt):
    return datetime(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=round_fifteen(dt.minute),
        second=0
    )


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
