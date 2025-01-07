import requests 
from config import TOMTOM_API_KEY, AQICN_API_KEY, OSRM_BASE_URL
import xml.etree.ElementTree as ET
import random

# List of vehicle types to be used for training
VEHICLE_TYPES = ["small_car", "large_car", "electric_car", "bus", "motorcycle", "train"]

def get_route_data(route_id, start_lat, start_lon, end_lat, end_lon, vehicle_type="small_car"):
    """
    Fetch route data and traffic information for a given route ID.
    """
    traffic_data = get_traffic_data(start_lat, start_lon)  # Fetch traffic data from TomTom API

    if not traffic_data:
        print("Error: No traffic data found.")
        return {}

    # Debug: Print the traffic data to inspect the structure
    print("Traffic Data:", traffic_data)

    # Extract relevant information safely
    try:
        current_speed = traffic_data.get("currentSpeed", None)
        free_flow_speed = traffic_data.get("freeFlowSpeed", None)
        current_travel_time = traffic_data.get("currentTravelTime", None)

        # Check if the data is found
        if current_speed is None or free_flow_speed is None or current_travel_time is None:
            print("Error: Missing essential traffic data.")
            return {}

        # Get route details (e.g., distance, duration)
        route_details = get_route_details(start_lat, start_lon, end_lat, end_lon)

        if not route_details:
            print("Error: No route details found.")
            return {}

        # Calculate emissions based on vehicle type and route details
        emissions = calculate_emissions(vehicle_type, route_details)

        route_data = {
            "route_id": route_id,
            "traffic_penalty": current_speed,  # Example: Traffic penalty based on current speed
            "time": current_travel_time,       # Example: Travel time
            "emissions": emissions,            # Emissions for the route based on vehicle type
        }

        return route_data

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}

def get_traffic_data(start_lat, start_lon):
    """
    Fetch traffic data from TomTom API and parse the XML response.
    """
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/xml?key={TOMTOM_API_KEY}&point={start_lat},{start_lon}"
    response = requests.get(url)

    # Log the response to see if it's valid
    print("Traffic API Response Status Code:", response.status_code)
    print("Traffic API Response Content:", response.text)  # Print the raw response

    if response.status_code == 200:
        try:
            # Parse the XML response
            root = ET.fromstring(response.text)
            
            # Extract the relevant data from the XML structure
            current_speed = root.find('.//currentSpeed').text
            free_flow_speed = root.find('.//freeFlowSpeed').text
            current_travel_time = root.find('.//currentTravelTime').text

            # Return the extracted data as a dictionary
            return {
                "currentSpeed": float(current_speed) if current_speed else None,
                "freeFlowSpeed": float(free_flow_speed) if free_flow_speed else None,
                "currentTravelTime": int(current_travel_time) if current_travel_time else None
            }

        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return {}
    else:
        print(f"Error: Unexpected response {response.status_code}.")
        print(f"Response content: {response.text}")
        return {}

def get_weather_data():
    """
    Fetch weather data from the AQICN API (Air Quality Index for Mumbai).
    """
    url = f"http://api.waqi.info/feed/mumbai/?token={AQICN_API_KEY}"
    response = requests.get(url)

    # Log the response to see if it's valid
    print("Weather API Response Status Code:", response.status_code)
    print("Weather API Response Content:", response.text)  # Print the raw response

    try:
        return response.json()
    except ValueError:
        print("Error parsing weather data response. Response content is not valid JSON.")
        return {}

def get_route_details(start_lat, start_lon, end_lat, end_lon):
    """
    Fetch route details (e.g., distance, duration) from the OSRM API.
    """
    url = f"{OSRM_BASE_URL}/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=false&steps=true"
    response = requests.get(url)

    # Log the response to see if it's valid
    print("OSRM API Response Status Code:", response.status_code)
    print("OSRM API Response Content:", response.text)  # Print the raw response

    try:
        return response.json()["routes"][0]  # Extract route details from the response
    except (ValueError, KeyError):
        print("Error parsing route details response. Response content is not valid JSON or missing routes.")
        return {}

def calculate_emissions(vehicle_type, route_details):
    """
    Calculate the emissions for a given vehicle type and route details.
    """
    EMISSION_FACTORS = {
        "small_car": 0.12,         # Small gasoline car
        "large_car": 0.21,         # Large gasoline car
        "electric_car": 0.05,      # Electric car (grid average)
        "bus": 0.05,               # Bus
        "train": 0.04,             # Train
        "domestic_flight": 0.25,   # Domestic flight
        "international_flight": 0.15,  # International flight
        "motorcycle": 0.10,        # Motorcycle
    }
    
    # Get the route distance (in meters)
    distance = route_details.get("distance", 0)  # distance is expected to be in meters

    # Default to small car if vehicle type is not found in the emission factors
    emission_factor = EMISSION_FACTORS.get(vehicle_type, 0.12)
    
    # Calculate emissions (grams of CO2)
    emissions = distance * emission_factor / 1000  # Convert from grams to kilograms for easier interpretation
    return emissions

def get_random_vehicle_type():
    """
    Returns a randomly selected vehicle type from the available list.
    """
    return random.choice(VEHICLE_TYPES)
