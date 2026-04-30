"""
HOS Calculator — 70hr/8day Property Carrier Rules
- 11 hour driving limit per day
- 14 hour on-duty window
- 30 minute rest break after 8 hours driving (cumulative)
- 10 hour off duty between shifts
- 70 hour / 8 day cycle
- Fuel stop every 1,000 miles
- 1 hour for pickup and dropoff
"""

# =========================
# VALIDATION FUNCTION
# =========================
def validate_input(total_miles, current_cycle_used, avg_speed):

    if not isinstance(total_miles, (int, float)):
        return "INVALID_INPUT: total_miles must be a number"

    if not isinstance(current_cycle_used, (int, float)):
        return "INVALID_INPUT: current_cycle_used must be a number"

    if not isinstance(avg_speed, (int, float)):
        return "INVALID_INPUT: avg_speed must be a number"

    if total_miles <= 0:
        return "INVALID_INPUT: total_miles must be greater than 0"

    if current_cycle_used < 0 or current_cycle_used > 70:
        return "INVALID_INPUT: current_cycle_used must be 0-70"

    if avg_speed <= 0 or avg_speed > 100:
        return "INVALID_INPUT: avg_speed must be 1-100"

    return None


# =========================
# MAIN CALCULATOR
# =========================
def calculate_trip(total_miles, current_cycle_used, avg_speed=55):

    # ---- VALIDATION ----
    error = validate_input(total_miles, current_cycle_used, avg_speed)
    if error:
        return {
            "error": error,
            "stops": [],
            "total_miles": 0,
            "total_trip_hours": 0,
            "total_days": 0
        }

    stops = []
    remaining_miles = total_miles
    miles_driven = 0
    total_hours_elapsed = 0

    hours_driven_today = 0
    hours_on_duty_today = 0
    hours_since_last_break = 0
    cycle_hours_used = current_cycle_used
    miles_since_fuel = 0

    day = 1

    # ---- PICKUP ----
    stops.append({
        'type': 'pickup',
        'location': 'Pickup Location',
        'start_hour': total_hours_elapsed,
        'duration': 1.0,
        'miles_from_start': 0,
        'day': day,
        'description': 'Loading / Pickup — 1 hour'
    })

    total_hours_elapsed += 1
    hours_on_duty_today += 1
    cycle_hours_used += 1

    # =========================
    # MAIN LOOP
    # =========================
    while remaining_miles > 0:

        # safety (avoid infinite loop)
        if remaining_miles < 0:
            break

        # ---- 70 HR RESET ----
        if cycle_hours_used >= 70:
            stops.append({
                'type': 'cycle_reset',
                'location': f'Rest Area — Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 34,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '34-hour restart'
            })

            total_hours_elapsed += 34

            cycle_hours_used = 0
            hours_driven_today = 0
            hours_on_duty_today = 0
            hours_since_last_break = 0
            continue

        # ---- 14 HOUR RULE ----
        if hours_on_duty_today >= 14:
            stops.append({
                'type': 'sleep',
                'location': f'Rest Stop — Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 10,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '10-hour off duty'
            })

            total_hours_elapsed += 10
            day += 1

            hours_driven_today = 0
            hours_on_duty_today = 0
            hours_since_last_break = 0
            continue

        # ---- 11 HOUR DRIVING LIMIT ----
        if hours_driven_today >= 11:
            stops.append({
                'type': 'sleep',
                'location': f'Rest Stop — Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 10,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '11hr limit rest'
            })

            total_hours_elapsed += 10
            day += 1

            hours_driven_today = 0
            hours_on_duty_today = 0
            hours_since_last_break = 0
            continue

        # ---- 30 MIN BREAK ----
        if hours_since_last_break >= 8:
            stops.append({
                'type': 'rest',
                'location': f'Rest Area — Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 0.5,
                'miles_from_start': miles_driven,
                'day': day,
                'description': '30-minute break'
            })

            total_hours_elapsed += 0.5
            hours_on_duty_today += 0.5
            cycle_hours_used += 0.5
            hours_since_last_break = 0
            continue

        # ---- FUEL STOP ----
        if miles_since_fuel >= 1000:
            stops.append({
                'type': 'fuel',
                'location': f'Fuel Station — Mile {miles_driven:.0f}',
                'start_hour': total_hours_elapsed,
                'duration': 0.5,
                'miles_from_start': miles_driven,
                'day': day,
                'description': 'Fuel stop'
            })

            total_hours_elapsed += 0.5
            hours_on_duty_today += 0.5
            cycle_hours_used += 0.5
            miles_since_fuel = 0
            hours_since_last_break = 0
            continue

        # ---- DRIVING ----
        max_drive = min(
            11 - hours_driven_today,
            14 - hours_on_duty_today,
            8 - hours_since_last_break,
            (1000 - miles_since_fuel) / avg_speed
        )

        max_drive = max(0.1, max_drive)

        drive_miles = min(remaining_miles, max_drive * avg_speed)
        drive_hours = drive_miles / avg_speed

        stops.append({
            'type': 'driving',
            'location': f'Mile {miles_driven:.0f} → Mile {miles_driven + drive_miles:.0f}',
            'start_hour': total_hours_elapsed,
            'duration': drive_hours,
            'miles_from_start': miles_driven,
            'miles_driven': drive_miles,
            'day': day,
            'description': f'Driving {drive_miles:.0f} miles'
        })

        miles_driven += drive_miles
        remaining_miles -= drive_miles
        total_hours_elapsed += drive_hours

        hours_driven_today += drive_hours
        hours_on_duty_today += drive_hours
        hours_since_last_break += drive_hours
        cycle_hours_used += drive_hours
        miles_since_fuel += drive_miles

    # ---- DROPOFF ----
    stops.append({
        'type': 'dropoff',
        'location': 'Dropoff Location',
        'start_hour': total_hours_elapsed,
        'duration': 1.0,
        'miles_from_start': miles_driven,
        'day': day,
        'description': 'Dropoff — 1 hour'
    })

    total_hours_elapsed += 1

    return {
        'stops': stops,
        'total_miles': total_miles,
        'total_trip_hours': total_hours_elapsed,
        'total_days': day,
        'avg_speed': avg_speed,
    }


# =========================
# DAILY LOGS GENERATOR
# =========================
def generate_daily_logs(trip_data):

    stops = trip_data['stops']
    daily_logs = {}

    for stop in stops:
        day = stop['day']

        if day not in daily_logs:
            daily_logs[day] = {
                'day': day,
                'off_duty': [],
                'driving': [],
                'on_duty_not_driving': [],
                'sleeper_berth': [],
                'total_miles': 0,
                'remarks': []
            }

        log = daily_logs[day]

        start = stop['start_hour'] % 24
        end = min(start + stop['duration'], 24)

        if stop['type'] == 'driving':
            log['driving'].append({'start': start, 'end': end})
            log['total_miles'] += stop.get('miles_driven', 0)
            log['remarks'].append(f"Driving: {stop['location']}")

        elif stop['type'] == 'sleep':
            log['off_duty'].append({'start': start, 'end': end})
            log['sleeper_berth'].append({'start': start, 'end': end})
            log['remarks'].append(f"Off Duty: {stop['location']}")

        else:
            log['on_duty_not_driving'].append({'start': start, 'end': end})
            log['remarks'].append(stop['description'])

    return list(daily_logs.values())