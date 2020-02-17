from pyze.api.schedule import ChargeSchedules, _minuteize, _deminuteize


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
