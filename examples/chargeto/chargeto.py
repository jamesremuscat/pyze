from pyze.api import Gigya, Kamereon, Vehicle, ChargeMode, ChargeState
from pyze.api.schedule import ChargeSchedules, ChargeSchedule, ScheduledCharge
import time
import dateutil
import os
import pytz

# What point to stop charging at, approximate - above this a charging schedule will be set to make sure the
# car doesn't charge. If fast charging it's possible that this will overshoot
MAX_CHARGE_THRESHOLD = os.getenv('MAX_CHARGE_THRESHOLD', 85)

# If the car drops below this number then it will change the charge mode to 'Always'
ALWAYS_CHARGE_AT_THRESHOLD = os.getenv('ALWAYS_CHARGE_AT_THRESHOLD', 65)

# If you want a specific VIN, specify it here or in the environment variables
SPECIFIC_VIN = os.getenv('SPECIFIC_VIN', False)

# The schedule is set in 'local time' this is the adjustment needed to correct your server time to that
# it's a hack but I run my server as UTC. If you are running on a machine with the same timezone as your car
# it should be set to 0
VEHICLE_TZ = os.getenv('VEHICLE_TZ', 'Europe/Paris')

#####################################################################################




#####################################################################################
## Set a charging schedule to start at epoch when and run for the duration
## specified (minutes)
def set_schedule( v, state, when, duration, blocking ):

    # round to previous 15 minutes, this ensures that the time passed is always in the window
    # and complies with API requirement for 15 minute blocks
    whenPrevious = (when - when%900)

    # make sure we don't call the API more than we need to
    if state.lastStart == whenPrevious and state.duration == duration:
        print( 'no need to update car schedule as same as requested setting' )
        return

    # if we are blocking then we will only adjust it if we are getting close to the
    # scheduled time, this uses current time not requested time to check
    if blocking:
        current_time = time.mktime(time.localtime())
        if state.lastStart > (current_time+(24*60*60)):
            print( 'no need to update schedule as it is more than one day to last blocking update',
                   time.strftime('%A %H:%M',time.localtime(state.lastStart)) if state.lastStart else '-',
                   time.strftime('%A %H:%M',time.localtime(whenPrevious)) )
            return

    # save into state as a cache
    state.lastStart = whenPrevious
    state.duration = duration
    
    # and figure out what we need to say to renault, lowercase day name and hour:minutes
    # the API thinks it is in Zulu time, but actually it is local time to the car
    # so we will format the time so it says 'Z' but IT IS THE TIME SET IN THE CAR
    # see also TZADJUST
    day_of_week = time.strftime('%A',time.localtime(whenPrevious)).lower()
    start = time.strftime('T%H:%MZ',time.localtime(whenPrevious))
    
    # Generate the schedule object, it will have just that day in it
    ISS = { 'activated': True }
    ISS[day_of_week] = { 'startTime': start, 'duration': duration }

    # Create a new blank set of schedules and add the one we just made to it
    schedules = ChargeSchedules()
    schedule = schedules.add(ChargeSchedule(ISS))

    print( 'scheduling on', day_of_week, '@', start, 'for', duration, 'minutes', '(to blocking charging)' if blocking else '')
    
    # send it to the car
    v.set_charge_schedules( schedules )
    v.set_charge_mode(ChargeMode.schedule_mode)

#####################################################################################
## main logic for determining what to do with the charge
def checkCharging(v,state):

    # Get current state from the car
    bs = v.battery_status()
    percentage = bs['batteryLevel']
    plugged_in = bs['plugStatus']
    charging = bs['chargingStatus']
    update_time = bs['timestamp']
    remaining_time = bs['chargingRemainingTime'] if 'chargingRemainingTime' in bs else 0
    instant_power = bs['chargingInstantaneousPower'] if 'chargingInstantaneousPower' in bs else None

    # and a timestamp for the calculations
    now = time.localtime()

    # check for rubbish back from the API, it has a rate limit and it's really easy to
    # exceed it especially if you use this and then refresh in the app a lot
    if not(percentage >= 0 and percentage <= 100):
        print( 'unable to check api:', bs )
        return

    # can we reliably estimate how long it will take?
    remaining_time_to_threshold_estimate = round((remaining_time / (100-percentage)) * (MAX_CHARGE_THRESHOLD - percentage),0) if percentage < MAX_CHARGE_THRESHOLD else 0

    # LOVE some logging 
    print( '{} {}% {}, {}, power: {} remaining: {} (ttc: {}min)  [updated: {}]'
           .format( time.strftime("%H:%M:%S",now),
                    percentage,
                    'plugged in' if plugged_in else '',
                    ChargeState(charging).name,
                    instant_power,
                    remaining_time,
                    remaining_time_to_threshold_estimate,
                    update_time))
    
    # make sure we always charge if we are getting low, otherwise
    # switch to a schedule (which we keep empty)
    if percentage < ALWAYS_CHARGE_AT_THRESHOLD:
        
        print( 'always charging as battery low' )
        if v.get_charge_mode() != ChargeMode.always_charging:
            print( 'setting charge mode' )
            v.set_charge_mode(ChargeMode.always_charging)
        
        # if we aren't charging but we are plugged in then try and get the car to start
        if charging < 0.2 and plugged_in > 0:
            print( 'requesting charge to start', charging, plugged_in )
            v.charge_start();
            
    else:
                    
        # we are scheduled but needing to charge some more
        # and we are plugged in, then we can set a schedule based on now
        if percentage < MAX_CHARGE_THRESHOLD:

            if plugged_in > 0:
                print( 'we should charge, setting 30 minute window from 15 minutes ago' )
                when = time.mktime(now)
            
                # schedule and ask the car to start charging if it isn't already charging
                set_schedule( v, state, when, 45, False );
                if charging < 0.2:
                    print( 'starting charging as not currently charging', charging )
                    v.charge_start();
                    
            else:
                print( 'wait to schedule charge till car is plugged in' )
                
        else:

            print( 'skipping charge as at ', percentage, '%' )

            # we do this by setting a charging time for 6 days from now
            when = time.mktime(now) + 6*24*3600 
            set_schedule( v, state, when, 15, True );
        

## This is used to keep track of what we have set as a schedule so
## we don't need to check what the car has set
class State:
    lastStart = 0
    duration = 0
    
state = State()

##################################################
# Set the timezone to the vehicle timezone, this may
# be different from the server
os.environ['TZ'] = VEHICLE_TZ
time.tzset()
            
##################################################
# Load the correct vehicle, this assumes there is only one,
# if there is more than one then set SPECIFIC_VIN (environment
# or top of this file)to be the one that matches your care pyze
# vehicles will give you a list
k = Kamereon()

if SPECIFIC_VIN:
    vin = SPECIFIC_VIN
else:
    vehicles = k.get_vehicles().get('vehicleLinks')
    vin = vehicles[0]['vin']

v = Vehicle(vin, k)

print ( 'Monitoring vehicle ', vin, 'in timezeone', time.tzname )

##################################################
## This is the main loop, it checks status and
## changes how the charging will behave
##################################################

while True:
    
    try:
        checkCharging(v,state)
        
    except (Exception, ArithmeticError) as e:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print (message)
        
    time.sleep( 5*60 ) # it doesn't need to be precise
