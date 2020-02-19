from pyze.api.schedule import ChargeSchedule, ChargeSchedules, _minuteize, \
    _deminuteize, ScheduledCharge, InvalidScheduleException, INITIAL_SCHEDULE, \
    round_fifteen

import dateparser
import pytest


def test_parse_schedules():
    raw_schedules = {
        "mode": "scheduled",
        "schedules": [{
            "id": 1,
            "activated": True,
            "monday": {
                "startTime": "T12:00Z",
                "duration": 15
            },
            "tuesday": {
                "startTime": "T04:30Z",
                "duration": 420
            },
            "wednesday": {
                "startTime": "T22:30Z",
                "duration": 420
            },
            "thursday": {
                "startTime": "T22:00Z",
                "duration": 420
            },
            "friday": {
                "startTime": "T12:15Z",
                "duration": 15
            },
            "saturday": {
                "startTime": "T12:30Z",
                "duration": 30
            },
            "sunday": {
                "startTime": "T12:45Z",
                "duration": 45
            }
        }]
    }

    schedules = ChargeSchedules(raw_schedules)

    assert len(schedules) == 1
    schedule = schedules[1]

    assert schedule['monday'].start_time == 'T12:00Z'
    assert schedule['monday'].duration == 15

    assert schedule['wednesday'].start_time == 'T22:30Z'
    assert schedule['wednesday'].duration == 420


def test_minuteize():
    assert _minuteize('T00:00Z') == 0
    assert _minuteize('T01:00Z') == 60
    assert _minuteize('T12:00Z') == (12 * 60)
    assert _minuteize('T23:59Z') == (24 * 60) - 1


def test_deminuteize():
    assert _deminuteize(0) == 'T00:00Z'
    assert _deminuteize(60) == 'T01:00Z'
    assert _deminuteize(12 * 60) == 'T12:00Z'
    assert _deminuteize((24 * 60) - 1) == 'T23:59Z'


def test_round_fifteen():
    assert round_fifteen(14) == 0
    assert round_fifteen(15) == 15
    assert round_fifteen(16) == 15

    assert round_fifteen(29) == 15
    assert round_fifteen(30) == 30
    assert round_fifteen(31) == 30


class TestScheduledCharge:
    def test_spans_midnight(self):
        before_midnight = ScheduledCharge('T23:30Z', 15)
        assert before_midnight.spans_midnight is False

        at_midnight = ScheduledCharge('T23:45Z', 15)
        assert at_midnight.spans_midnight is True

        after_midnight = ScheduledCharge('T23:45Z', 30)
        assert after_midnight.spans_midnight is True

    def test_finish_time(self):
        at_midnight = ScheduledCharge('T23:45Z', 15)
        assert at_midnight.finish_time == 'T00:00Z'
        assert at_midnight.finish_time_minutes == 0

        after_midnight = ScheduledCharge('T23:45Z', 30)
        assert after_midnight.finish_time == 'T00:15Z'
        assert after_midnight.finish_time_minutes == 15

        same_day = ScheduledCharge('T12:00Z', 60)
        assert same_day.finish_time == 'T13:00Z'
        assert same_day.finish_time_minutes == (13 * 60)

    def test_validation(self):
        with pytest.raises(InvalidScheduleException, match=r".*not a valid start time.*"):
            ScheduledCharge('1200', 15).validate()
        with pytest.raises(InvalidScheduleException, match=r".*not a valid start time.*"):
            ScheduledCharge(1200, 15).validate()
        with pytest.raises(InvalidScheduleException, match=r".*not a valid start time.*"):
            ScheduledCharge('T24:00Z', 15).validate()
        with pytest.raises(InvalidScheduleException, match=r".*not a valid start time.*"):
            ScheduledCharge('T12:04Z', 15).validate()

        with pytest.raises(InvalidScheduleException, match=r".*not a valid duration.*"):
            ScheduledCharge('T12:00Z', 14).validate()
        with pytest.raises(InvalidScheduleException, match=r".*not a valid duration.*"):
            ScheduledCharge('T12:00Z', 16).validate()
        with pytest.raises(InvalidScheduleException, match=r".*not a valid duration.*"):
            ScheduledCharge('T12:00Z', -1).validate()
        with pytest.raises(InvalidScheduleException, match=r".*not a valid duration.*"):
            ScheduledCharge('T12:00Z', '15').validate()

    def test_between(self):
        sc = ScheduledCharge.between(
            dateparser.parse('17:00'),
            dateparser.parse('21:00')
        )

        assert sc.start_time == 'T17:00Z'
        assert sc.duration == 240

        sc2 = ScheduledCharge.between(
            dateparser.parse('23:05'),
            dateparser.parse('03:31 tomorrow')
        )

        assert sc2.start_time == 'T23:00Z'
        assert sc2.finish_time == 'T03:30Z'
        assert sc2.duration == 270

        with pytest.raises(RuntimeError, match=r"Expected start to be a datetime.*"):
            ScheduledCharge.between(
                '23:00',
                dateparser.parse('03:30 tomorrow')
            )

        with pytest.raises(RuntimeError, match=r"Expected end to be a datetime.*"):
            ScheduledCharge.between(
                dateparser.parse('23:00'),
                '03:30 tomorrow'
            )

        with pytest.raises(RuntimeError, match='Start time should be before end time'):
            ScheduledCharge.between(
                dateparser.parse('23:00'),
                dateparser.parse('03:30')
            )

    def test_overlaps(self):
        first = ScheduledCharge.between(
            dateparser.parse('23:00'),
            dateparser.parse('01:00 tomorrow')
        )
        second = ScheduledCharge.between(
            dateparser.parse('00:30 tomorrow'),
            dateparser.parse('02:00 tomorrow')
        )

        assert first.overlaps(second) is True
        assert second.overlaps(first) is False


class TestCreatingFromNew():
    def test_create_schedules(self):
        cs = ChargeSchedules()
        assert len(cs) == 0

    def test_create_schedule(self):
        cs = ChargeSchedules()

        sch = cs.new_schedule()
        assert sch.id == 1
        assert sch['monday'].start_time == 'T12:00Z'
        assert sch['wednesday'].duration == 15

        assert sch.validate() is True
        assert cs.validate() is True

        sch2 = cs.new_schedule()
        assert sch2.id == 2


class TestChargeSchedule():
    def test_create_new(self):
        cs = ChargeSchedule()
        assert cs['monday'].start_time == 'T12:00Z'
        cs.validate()

    def test_validates_overlap(self):
        cs = ChargeSchedule()

        cs['monday'].start_time = 'T23:45Z'
        cs['monday'].duration = 30

        cs['tuesday'].start_time = 'T00:00Z'

        with pytest.raises(
            InvalidScheduleException,
            match='Charge for monday overlaps charge for tuesday'
        ):
            cs.validate()

    def test_set_item(self):
        cs = ChargeSchedule()

        sch = ScheduledCharge('T07:30Z', 120)

        with pytest.raises(RuntimeError, match=r".*not a valid day"):
            cs['florsday'] = sch

        with pytest.raises(RuntimeError, match=r"Expected ScheduledCharge, got.*"):
            cs['friday'] = 1138

        cs['friday'] = sch
        assert cs['friday'] == sch

    def test_for_json(self):
        cs = ChargeSchedule()
        expected = INITIAL_SCHEDULE.copy()
        expected['id'] = None
        assert cs.for_json() == expected

        # New API allows days to have no scheduled charges
        # see https://github.com/jamesremuscat/pyze/issues/46
        del cs['monday']
        del expected['monday']
        assert cs.for_json() == expected
