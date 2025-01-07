import gym
from gym import spaces
import numpy as np
import random
from api_integration import get_route_data, get_weather_data, VEHICLE_TYPES

# Define Mumbai's latitude and longitude bounds
MUMBAI_LAT_MIN = 18.5
MUMBAI_LAT_MAX = 19.5
MUMBAI_LON_MIN = 72.5
MUMBAI_LON_MAX = 73.5

def generate_random_location(lat_min, lat_max, lon_min, lon_max):
    """
    Generates a random location (latitude, longitude) within the given bounds.
    """
    lat = random.uniform(lat_min, lat_max)
    lon = random.uniform(lon_min, lon_max)
    return lat, lon

class RouteOptimizationEnv(gym.Env):
    def __init__(self):
        super(RouteOptimizationEnv, self).__init__()

        # Initialize the state by calling reset, which fetches the routes and initializes coordinates
        self.state = self.reset()

        # Initialize the action space based on available routes
        self.action_space = spaces.Discrete(len(self.routes))  # Set the action space to the number of available routes

        # Define the observation space based on state representation
        self.observation_space = spaces.Box(low=0, high=1, shape=(4 + len(VEHICLE_TYPES),), dtype=np.float32)

        # Initialize done status
        self.done = False

    def fetch_routes(self):
        """
        Fetch multiple route options from the OSRM API.
        """
        routes = []
        for i in range(3):  # Fetch 3 alternative routes
            # Randomly select a vehicle type for the route
            vehicle_type = random.choice(VEHICLE_TYPES)
            # Ensure all parameters are passed to get_route_data
            route_details = get_route_data(self.start_lat, self.start_lon, self.end_lat, self.end_lon, vehicle_type)
            route_with_id = {
                'id': i,  # Assign a unique ID
                'route': route_details,  # Store the entire route details
                'vehicle_type': vehicle_type  # Store the vehicle type as part of the route
            }
            routes.append(route_with_id)
        return routes

    def reset(self):
        """
        Resets the environment to its initial state with random start and end locations within Mumbai.
        """
        # Generate random start and end locations within Mumbai
        self.start_lat, self.start_lon = generate_random_location(MUMBAI_LAT_MIN, MUMBAI_LAT_MAX, MUMBAI_LON_MIN, MUMBAI_LON_MAX)
        self.end_lat, self.end_lon = generate_random_location(MUMBAI_LAT_MIN, MUMBAI_LAT_MAX, MUMBAI_LON_MIN, MUMBAI_LON_MAX)

        # Fetch the available routes for this configuration
        self.routes = self.fetch_routes()

        # Fetch the state data with the vehicle type of the first route
        self.state = self.fetch_state_data(self.routes[0]['vehicle_type'])
        self.done = False
        return self.state

    def step(self, action):
        """
        Takes an action, interacts with the environment, and returns the next state and reward.
        """
        selected_route = self.routes[action]
        route_id = selected_route['id']
        route_details = selected_route['route']
        vehicle_type = selected_route['vehicle_type']  # Get the selected vehicle type for this route

        # Get route data (traffic, time, etc.)
        route_data = get_route_data(route_id, self.start_lat, self.start_lon, self.end_lat, self.end_lon, vehicle_type=vehicle_type)
        if not route_data:
            return self.state, 0, True, {}  # If route data is unavailable, return zero reward and terminate

        travel_time, emissions, traffic_penalty = route_data["time"], route_data["emissions"], route_data["traffic_penalty"]

        # Calculate reward (negative because we're optimizing for lower values)
        reward = -1 * (travel_time + emissions + traffic_penalty)

        # Update state with weather data and vehicle type included
        self.state = self.fetch_state_data(vehicle_type)

        # Check if destination is reached
        if self.is_at_destination():
            self.done = True
        else:
            self.done = False

        return self.state, reward, self.done, {}

    def is_at_destination(self):
        """
        Checks if the current location is close enough to the destination.
        """
        # A simple check to see if the agent is close enough to the destination
        return abs(self.start_lat - self.end_lat) < 0.01 and abs(self.start_lon - self.end_lon) < 0.01

    def fetch_state_data(self, vehicle_type):
        """
        Fetch dynamic state data (traffic, weather, etc.), and include vehicle type.
        """
        # Fetch route data for the given vehicle type
        route_data = get_route_data(0, self.start_lat, self.start_lon, self.end_lat, self.end_lon, vehicle_type=vehicle_type)

        if not route_data:
            return np.zeros(4 + len(VEHICLE_TYPES), dtype=np.float32)  # Return zeroed state if no data

        travel_time = route_data.get("time", 0)
        emissions = route_data.get("emissions", 0)
        traffic_penalty = route_data.get("traffic_penalty", 0)

        # Fetch weather data
        weather_data = get_weather_data()  # Weather data will be added to the state
        air_quality_index = weather_data.get("data", {}).get("aqi", 0)  # Assuming the API returns 'aqi'

        # One-hot encode the vehicle type
        vehicle_type_index = VEHICLE_TYPES.index(vehicle_type)
        vehicle_type_one_hot = np.zeros(len(VEHICLE_TYPES))
        vehicle_type_one_hot[vehicle_type_index] = 1

        # Create the state representation (now includes weather data and vehicle type)
        state = np.array([travel_time, emissions, traffic_penalty, air_quality_index] + vehicle_type_one_hot.tolist(), dtype=np.float32)
        return state
