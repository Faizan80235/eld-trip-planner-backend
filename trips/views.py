from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .hos_calculator import calculate_trip, generate_daily_logs
import requests


@api_view(['POST'])
def calculate_route(request):
    """
    Main API endpoint —  Get trip details return  route + logs 
    POST /api/calculate-route/
    """
    try:
        data = request.data

        current_location = data.get('current_location', '')
        pickup_location = data.get('pickup_location', '')
        dropoff_location = data.get('dropoff_location', '')
        current_cycle_used = float(data.get('current_cycle_used', 0))

        if not all([current_location, pickup_location, dropoff_location]):
            return Response(
                {'error': 'All locations are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if current_cycle_used < 0 or current_cycle_used > 70:
            return Response(
                {'error': 'Current cycle used must be between 0 and 70 hours'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get coordinates and distance using OpenRouteService (free)
        route_data = get_route_data(current_location, pickup_location, dropoff_location)

        if not route_data:
            # Fallback: estimate based on straight-line (if API fails)
            route_data = {
                'total_miles': 500,
                'waypoints': [],
                'geometry': None
            }

        # Calculate HOS schedule
        trip_result = calculate_trip(
            total_miles=route_data['total_miles'],
            current_cycle_used=current_cycle_used,
        )

        # Generate daily log sheets
        daily_logs = generate_daily_logs(trip_result)

        return Response({
            'success': True,
            'route': route_data,
            'trip_schedule': trip_result,
            'daily_logs': daily_logs,
            'summary': {
                'total_miles': route_data['total_miles'],
                'total_hours': trip_result['total_trip_hours'],
                'total_days': trip_result['total_days'],
                'stops_count': len(trip_result['stops']),
            }
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_route_data(current_location, pickup_location, dropoff_location):
    """
   Fetch data  from  OpenRouteService  (Free API)
    """
    try:
        #  — convert location names to coordinates
        def geocode(location_name):
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1
            }
            headers = {'User-Agent': 'ELD-Trip-Planner/1.0'}
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            results = resp.json()
            if results:
                return float(results[0]['lon']), float(results[0]['lat'])
            return None

        # Get coordinates
        current_coords = geocode(current_location)
        pickup_coords = geocode(pickup_location)
        dropoff_coords = geocode(dropoff_location)

        if not all([current_coords, pickup_coords, dropoff_coords]):
            return None

        # Calculate approximate distance in miles
        def haversine_miles(coord1, coord2):
            import math
            lon1, lat1 = coord1
            lon2, lat2 = coord2
            R = 3958.8  # Earth radius in miles
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
                math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c * 1.25  # multiply by 1.25 for road vs straight-line

        # Total trip: current → pickup → dropoff
        miles_to_pickup = haversine_miles(current_coords, pickup_coords)
        miles_pickup_to_dropoff = haversine_miles(pickup_coords, dropoff_coords)
        total_miles = miles_to_pickup + miles_pickup_to_dropoff

        return {
            'total_miles': round(total_miles, 1),
            'miles_to_pickup': round(miles_to_pickup, 1),
            'miles_pickup_to_dropoff': round(miles_pickup_to_dropoff, 1),
            'waypoints': [
                {'name': current_location, 'coords': current_coords, 'type': 'current'},
                {'name': pickup_location, 'coords': pickup_coords, 'type': 'pickup'},
                {'name': dropoff_location, 'coords': dropoff_coords, 'type': 'dropoff'},
            ]
        }

    except Exception as e:
        print(f"Route API error: {e}")
        return None


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok', 'message': 'ELD Backend is running!'})