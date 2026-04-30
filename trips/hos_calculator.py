"""
HOS Calculator - 70hr/8day Property Carrier Rules
- 11 hour driving limit per day
- 14 hour on-duty window
- 30 minute rest break after 8 hours driving
- 10 hour off duty between shifts
- 70 hour / 8 day cycle
- Fuel stop every 1,000 miles
- 1 hour for pickup and dropoff
"""


def calculate_trip(total_miles, current_cycle_used, avg_speed=55):
    """
    Calculates the full trip schedule based on FMCSA HOS rules.
    Returns: dict with stops list and trip summary
    """
    stops = []
    remaining_miles = total_miles
    miles_driven = 0
    total_hours_elapsed = 0

    # Daily tracking variables
    hours_driven_today = 0
    hours_on_duty_today = 0
    hours_since_last_break = 0
    cycle_hours_used = current_cycle_used
    miles_since_fuel = 0

    # Day counter
    day = 1

    # Track miles driven per day for log sheets
    miles_per_day = {1: 0}

    # --- PICKUP STOP (1 hour) ---
    stops.append({
        'type': 'pickup',
        'location': 'Pickup Location',
        'start_hour': total_hours_elapsed,
        'duration': 1.0,
        'miles_from_start': 0,
        'day': day,
        'description': 'Loading / Pickup - 1 hour'
    })
    total_hours_elapsed += 1.0
    hours_on_duty_today += 1.0
    cycle_hours_used += 1.0

    # --- MAIN DRIVING LOOP ---
    while remaining_miles > 0:

        # Check: 70hr cycle limit reached?
        if cycle_hours_used >= 70:
            stops.append({
                'type': 'cycle_reset',
                'location': f'Rest Area - Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 34.0,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '34-hour restart - 70hr cycle reset'
            })
            total_hours_elapsed += 34.0
            cycle_hours_used = 0
            hours_driven_today = 0
            hours_on_duty_today = 0
            hours_since_last_break = 0
            day += int(34 / 24) + 1
            if day not in miles_per_day:
                miles_per_day[day] = 0
            continue

        # Check: 14hr on-duty window reached?
        if hours_on_duty_today >= 14:
            off_duration = 10.0
            stops.append({
                'type': 'sleep',
                'location': f'Rest Stop - Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': off_duration,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '10-hour off duty - New driving day starts'
            })
            total_hours_elapsed += off_duration
            hours_driven_today = 0
            hours_on_duty_today = 0
            hours_since_last_break = 0
            day += 1
            if day not in miles_per_day:
                miles_per_day[day] = 0
            continue

        # Check: 11hr driving limit reached today?
        if hours_driven_today >= 11:
            off_duration = 10.0
            stops.append({
                'type': 'sleep',
                'location': f'Rest Stop - Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': off_duration,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '10-hour off duty - 11hr limit reached'
            })
            total_hours_elapsed += off_duration
            hours_driven_today = 0
            hours_on_duty_today = 0
            hours_since_last_break = 0
            day += 1
            if day not in miles_per_day:
                miles_per_day[day] = 0
            continue

        # Check: 30-min break required after 8 cumulative driving hours?
        if hours_since_last_break >= 8:
            stops.append({
                'type': 'rest',
                'location': f'Rest Area - Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 0.5,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '30-minute mandatory rest break'
            })
            total_hours_elapsed += 0.5
            hours_on_duty_today += 0.5
            cycle_hours_used += 0.5
            hours_since_last_break = 0
            continue

        # Check: Fuel stop required every 1,000 miles?
        if miles_since_fuel >= 1000:
            stops.append({
                'type': 'fuel',
                'location': f'Fuel Station - Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 0.5,
                'miles_from_start': miles_driven,
                'day': day,
                'description': 'Fuel stop - every 1,000 miles'
            })
            total_hours_elapsed += 0.5
            hours_on_duty_today += 0.5
            cycle_hours_used += 0.5
            miles_since_fuel = 0
            continue

        # Calculate maximum drivable hours in this session
        max_drive_this_session = min(
            11 - hours_driven_today,                # daily 11hr limit
            14 - hours_on_duty_today,               # 14hr window
            8 - hours_since_last_break,             # break rule
            (1000 - miles_since_fuel) / avg_speed,  # fuel stop interval
        )
        max_drive_this_session = max(0.1, max_drive_this_session)

        # Calculate miles for this driving session
        max_miles_this_session = max_drive_this_session * avg_speed
        drive_miles = min(remaining_miles, max_miles_this_session)
        drive_hours = drive_miles / avg_speed

        # Add driving segment
        stops.append({
            'type': 'driving',
            'location': f'Mile {miles_driven:.0f} to Mile {miles_driven + drive_miles:.0f}',
            'start_hour': total_hours_elapsed,
            'duration': drive_hours,
            'miles_from_start': miles_driven,
            'drive_miles': drive_miles,
            'day': day,
            'description': f'Driving {drive_miles:.0f} miles ({drive_hours:.1f} hrs)'
        })

        # Update all counters
        miles_driven += drive_miles
        remaining_miles -= drive_miles
        total_hours_elapsed += drive_hours
        hours_driven_today += drive_hours
        hours_on_duty_today += drive_hours
        hours_since_last_break += drive_hours
        cycle_hours_used += drive_hours
        miles_since_fuel += drive_miles

        # Track miles driven per day
        miles_per_day[day] = miles_per_day.get(day, 0) + drive_miles

    # --- DROPOFF STOP (1 hour) ---
    stops.append({
        'type': 'dropoff',
        'location': 'Dropoff Location',
        'start_hour': total_hours_elapsed,
        'duration': 1.0,
        'miles_from_start': miles_driven,
        'day': day,
        'description': 'Unloading / Dropoff - 1 hour'
    })
    total_hours_elapsed += 1.0

    return {
        'stops': stops,
        'total_miles': total_miles,
        'total_trip_hours': total_hours_elapsed,
        'total_days': day,
        'avg_speed': avg_speed,
        'miles_per_day': miles_per_day,
    }


def generate_daily_logs(trip_data):
    """
    Generates daily log sheets for each day of the trip.
    Handles multi-day stops (34hr restart, 10hr sleep) correctly
    by splitting them across calendar days.
    Returns: list of daily log entries
    """
    stops = trip_data['stops']
    miles_per_day = trip_data.get('miles_per_day', {})
    daily_logs = {}

    def ensure_day(d):
        """Initialize a day log entry if it does not exist."""
        if d not in daily_logs:
            daily_logs[d] = {
                'day': d,
                'off_duty': [],
                'driving': [],
                'on_duty_not_driving': [],
                'sleeper_berth': [],
                'total_miles': round(miles_per_day.get(d, 0)),
                'remarks': []
            }

    for stop in stops:
        day = stop['day']
        ensure_day(day)

        start_hour = stop['start_hour']
        duration = stop['duration']
        stop_type = stop['type']

        # Split multi-day stops across calendar days
        remaining_duration = duration
        current_hour = start_hour
        current_day = day

        while remaining_duration > 0:
            ensure_day(current_day)
            log = daily_logs[current_day]

            hour_of_day = current_hour % 24
            hours_left_in_day = 24 - hour_of_day
            chunk = min(remaining_duration, hours_left_in_day)
            end_of_chunk = hour_of_day + chunk

            if stop_type == 'driving':
                log['driving'].append({'start': hour_of_day, 'end': end_of_chunk})
                if current_day == day:
                    log['remarks'].append(f"Driving: {stop['location']}")

            elif stop_type == 'sleep':
                log['sleeper_berth'].append({'start': hour_of_day, 'end': end_of_chunk})
                if current_day == day:
                    log['remarks'].append(f"Off Duty / Sleep: {stop['location']}")

            elif stop_type == 'cycle_reset':
                log['off_duty'].append({'start': hour_of_day, 'end': end_of_chunk})
                if current_day == day:
                    log['remarks'].append(f"34-hr Restart: {stop['location']}")

            elif stop_type in ('pickup', 'dropoff', 'fuel', 'rest'):
                log['on_duty_not_driving'].append({'start': hour_of_day, 'end': end_of_chunk})
                if current_day == day:
                    log['remarks'].append(f"{stop['description']}: {stop['location']}")

            remaining_duration -= chunk
            current_hour += chunk
            if remaining_duration > 0:
                current_day += 1

    return list(daily_logs.values())