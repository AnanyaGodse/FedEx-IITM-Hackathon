from flask import Flask, request, jsonify
from stable_baselines3 import DQN
from environment import RouteOptimizationEnv
from api_integration import get_route_data

app = Flask(__name__)

# Load the trained model
model = DQN.load("models/dqn_route_optimization")

@app.route("/optimize_route", methods=["POST"])
def optimize_route():
    # Get data from the POST request (user input)
    data = request.json
    start_lat = data.get("start_lat")
    start_lon = data.get("start_lon")
    end_lat = data.get("end_lat")
    end_lon = data.get("end_lon")
    vehicle_type = data.get("vehicle_type")

    # Ensure all required fields are provided
    if not all([start_lat, start_lon, end_lat, end_lon, vehicle_type]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    # Initialize environment with real-time data (dynamically using user input)
    env = RouteOptimizationEnv(start_lat=start_lat, start_lon=start_lon, end_lat=end_lat, end_lon=end_lon)
    
    # Fetch the initial state
    state = env.reset()

    # Predict best route based on the environment's current state
    action, _ = model.predict(state)

    # Get the route details for the recommended route
    selected_route = env.routes[action]
    route_data = selected_route['route']  # Get route details from the selected route
    
    if not route_data:
        return jsonify({"error": "Failed to fetch route data"}), 500

    # Prepare the response with the recommended route and additional information
    response = {
        "recommended_route": selected_route['id'],
        "route_details": route_data
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)


