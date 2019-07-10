def _parse_schedule(data):
    schedule = {}

    for day, charge_times in data.get('calendar', {}).items():
        schedule[day] = [ScheduledCharge(t['startTime'], t['duration']) for t in charge_times]

    return schedule


DAYS = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday'
]

MINUTES_IN_DAY = 60 * 24


class ChargeSchedule(object):
    def __init__(self, data):
        self._schedule = _parse_schedule(data)

    def validate(self):
        for day, charge_times in self._schedule.items():
            # Validate each individual schedule entry...
            for charge_time in charge_times:
                charge_time.validate()

            # ... and the schedule as a whole has no overlaps or gaps
            if len(charge_times) != 1:
                raise InvalidScheduleException('{} charges scheduled for {} (must be exactly 1)'.format(len(charge_times), day))

            if charge_times[0].spans_midnight:
                next_day = DAYS[(DAYS.index(day) + 1) % len(DAYS)]
                print('Today is {}, tomorrow is {}'.format(day, next_day))
                tomorrow_charge = self._schedule[next_day][0]
                if charge_times[0].overlaps(tomorrow_charge):
                    raise InvalidScheduleException('Charge for {} overlaps charge for {}'.format(day, next_day))
        return True

    def __getitem__(self, key):
        return self._schedule[key]

    def __setitem__(self, key, value):
        if key not in DAYS:
            raise RuntimeError('{} is not a valid day'.format(key))
        if not isinstance(value, ScheduledCharge):
            raise RuntimeError('Expected ScheduledCharge, got {} instead'.format(value.__class__))

        # Note: we must allow the schedule to be invalidated here as it might require subsequent assignments
        # to make it valid (or else risk it being essentially immutable without gymnastics).
        self._schedule[key] = value

    def __repr__(self):
        return '<ChargeSchedule {}>'.format(self._schedule)


class ScheduledCharge(object):
    def __init__(self, start_time, duration):
        self.start_time = start_time
        self.duration = duration

    def validate(self):
        _validate_start_time(self.start_time)
        _validate_duration(self.duration)

    @property
    def spans_midnight(self):
        start = _minuteize(self.start_time)
        finish = start + self.duration
        return finish >= MINUTES_IN_DAY

    @property
    def finish_time_minutes(self):
        start = _minuteize(self.start_time)
        finish = start + self.duration
        return finish % MINUTES_IN_DAY

    def overlaps(self, other):
        return self.finish_time_minutes >= _minuteize(other.start_time)

    def __repr__(self):
        return '(Start {}, duration {})'.format(self.start_time, self.duration)


class InvalidScheduleException(Exception):
    pass


def _validate_start_time(start_time):
    if isinstance(start_time, str):
        if len(start_time) == 4:
            hour = start_time[0:2]
            minute = start_time[2:4]

            if int(hour) < 24:
                if minute in ['00', '15', '30', '45']:
                    return True
    raise InvalidScheduleException("{} is not a valid start time".format(start_time))


def _validate_duration(duration):
    if isinstance(duration, int):
        if duration % 15 == 0:
            return True
    raise InvalidScheduleException("{} is not a valid duration".format(duration))


def _minuteize(timestr):
    return (int(timestr[:2]) * 60) + int(timestr[2:])


def _deminuteize(tval):
    return '{:02g}{:02g}'.format(
        math.floor(tval / 60),
        tval % 60
    )
