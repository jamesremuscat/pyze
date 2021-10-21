# How does it work

The script polls the API for charge status and then will use charge
scheduling to either charge or block charging of the car. If the
battery is lower than the lowest threshold the script will change the
car setting to be 'always charging' an disable the schedule

Once the charge goes above this threshold the script then sets a
rolling charge window and monitors the battery percentage every 5
minutes. It will continue to move this window as the car charges.

If the percentage reaches the maximum configured it will change the
scheduled time to be yesterday. This will stop the charging the next
time the car refreshes - which is about every 10 minutes. Therefore
there may be an overshoot on cars that are charging very quickly. At
11kw it normally stops within 1%. By setting the threshold to
something around 85% it should have stopped charging before the
regenerative braking becomes disabled at 90%.

NOTE: the API is rate limited, do not refresh in the App too often or
run pyze status in parallel to many times or you may find yourself
locked out. It can take a while for the limit to clear and the script
will resume working when it does - note that it will not be able to
stop charging during the lockout period!

NOTE: The API is pretty poor at the best of times so there are no
promises your car will start or stop charging at the right times!

If you must have a charged car then this is probably not the best option
for you....

# Configuration

There are two parts to the configuration process - the first is
setting the environment variables used by the API and the script, the
second is logging in

## Environment Variables

```
KAMEREON_API_KEY=<>
GIGYA_API_KEY=3_<>
```
API keys required to connect to the Renault API, see main documentation and also issue id #95

```
KAMERON_ACCOUNT_ID=<>
SPECIFIC_VIN=<>
```
You may need to configure these depending on your account
setup. KAMERON_ACCOUNT_ID= is pyze compatible, SPECIFIC_VIN is for
this code only - you can get a list of VINs by running `pyze
vehicles`.  By default it will always pick the first configured
vehicle

```
VEHICLE_TZ=Europe/Stockholm
```
The timezone for the car, this will override the local timezone for the server which can
be useful if the server isn't where the car is, or if the server is UTC

## Logging into the API

```
pyze login
```
This script uses the same login credentials as the pyze command line script so simply make sure
the pyze command line works (see main readme) and then this script should work

## Other configuration environment variables

```
MAX_CHARGE_THRESHOLD=85
```
What point to stop charging at, approximate - above this a charging
schedule will be set to make sure the car doesn't charge. If fast
charging it's possible that this will overshoot

```
ALWAYS_CHARGE_AT_THRESHOLD=65
```
If the car drops below this number then it will change the charge mode
to 'Always'

# Running

Once you have configured the script and logged in using `pyze login` you
just run the script. It will loop indefinately. You may want to find a nice
way to run it as a background process, I just run it in screen/tmux so I
can see the console output

```
python38 chargeto.py
```

As this is a demo it doesn't do nice things like logging to syslog
or running in the background automatically

# Output

```
10:49:32 86% plugged in, Waiting for planned charge, power: 11.5 remaining: 55 (ttc: 12.0min)  [updated: 2021-10-21T10:48:57Z]
we should charge, setting 30 minute window from 15 minutes ago
scheduling on thursday @ T12:45Z for 45 minutes
starting charging as not currently charging 0.1
```

First line is status line, this is printed every 5 minutes. It consists of:
Car local time, % battery, plug state, charge state, charge speed and remaining time. ttc is the estimate time to MAX_CHARGE_THRESHOLD
and updated is the last time the car talked to the API

Then it says what it things should happen. Threshold is set to 89% for this example so it will try and charge, windows
are set on 15 minute barriers because of old Zoes, newer ones don't care but the API does

And it will explicitly ask the car to charge because it isn't but is plugged in.

You can confirm that the car picked up the command by making sure the updated timestamp changed after a command was issued
(eg in this output the next line it says 10:50 which means it did as that's after the 10:49 the command was issued at)

```
10:54:35 86% plugged in, Charging, power: 11.5 remaining: 55 (ttc: 12.0min)  [updated: 2021-10-21T10:50:53Z]
we should charge, setting 30 minute window from 15 minutes ago
no need to update car schedule as same as requested setting
10:59:36 86% plugged in, Charging, power: 11.5 remaining: 55 (ttc: 12.0min)  [updated: 2021-10-21T10:50:53Z]
we should charge, setting 30 minute window from 15 minutes ago
no need to update car schedule as same as requested setting
```

Regular polling checks. Note the updated time hasn't changed which means the car hasn't reported anything so no decisions
are changed. The script doesn't check this time so will assume more charging is still needed!

It's normal for the car to report in less often than the poll interval - normally it is every 10-15 minutes when
charging and it can be slower otherwise. It will also report in when car parks and is plugged in. You can
manually wake the car up by using the remote to turn lights on and off or lock and unlock the car.


```
11:04:37 89% plugged in, Charging, power: 11.5 remaining: 50 (ttc: 0min)  [updated: 2021-10-21T11:04:19Z]
skipping charge as at  89 %
scheduling on wednesday @ T13:00Z for 15 minutes (to blocking charging)
```
Now the car has reported it, and we have hit our threshold so the script changes the schedule to say
charge yesterday which will stop it!

```
11:09:38 89% plugged in, Waiting for planned charge, power: 11.5 remaining: 50 (ttc: 0min)  [updated: 2021-10-21T11:05:21Z]
skipping charge as at  89 %
no need to update car schedule as same as requested setting
11:14:39 89% plugged in, Waiting for planned charge, power: 11.5 remaining: 50 (ttc: 0min)  [updated: 2021-10-21T11:05:21Z]
skipping charge as at  89 %
no need to update car schedule as same as requested setting
```
These are normal status lines, the charging stopped (Waiting for planned charge)



