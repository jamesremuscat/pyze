from collections import namedtuple
from pyze.api.schedule import ChargeSchedules
from pyze.cli.schedule import show


def test_show(capsys):
    valid_gappy_schedules = {
        "mode": "always",
        "schedules": [
            {
                "id": 1,
                "activated": True,
                "monday": {
                    "startTime": "T23:30Z",
                    "duration": 60
                },
                "thursday": {
                    "startTime": "T01:00Z",
                    "duration": 120
                }
            },
            {
                "id": 2,
                "activated": False
            },
            {
                "id": 3,
                "activated": False
            },
            {
                "id": 4,
                "activated": False
            },
            {
                "id": 5,
                "activated": False
            }
        ]
    }

    cs = ChargeSchedules(valid_gappy_schedules)
    show(cs, None, namedtuple('parsed_args', ['utc'])(False))

    output = capsys.readouterr()

    expected_out = '''
Schedule ID: 1 [Active]
Day       Start time    End time    Duration
--------  ------------  ----------  ----------
Monday    23:30         00:30+      1:00:00
Thursday  01:00         03:00       2:00:00

Schedule ID: 2
Day    Start time    End time    Duration
-----  ------------  ----------  ----------

Schedule ID: 3
Day    Start time    End time    Duration
-----  ------------  ----------  ----------

Schedule ID: 4
Day    Start time    End time    Duration
-----  ------------  ----------  ----------

Schedule ID: 5
Day    Start time    End time    Duration
-----  ------------  ----------  ----------

'''.strip()

    assert output.out.strip() == expected_out
