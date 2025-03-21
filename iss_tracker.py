import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional
import json

import requests
import xmltodict
import redis
import math
from geopy.geocoders import Nominatim
from dateutil import parser
from flask import Flask, request, jsonify


ISS_DATA_URL = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"

app = Flask(__name__)

r = redis.Redis(host='redis-db', port=6379, db=0, decode_responses=True) # Redis (b'string') decode responses into strings

def setup_logging():
    logging.basicConfig(
        filename="iss_tracker.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

setup_logging()

def fetch_iss_data() -> Optional[List[Dict[str, Any]]]:
    """
    Fetch ISS state vector data from NASA's API and parse it into a list of dictionaries.
    
    Returns:
        Optional[List[Dict[str, Any]]]: Parsed ISS state vectors, or None if request fails.
    """
    try:
        response = requests.get(ISS_DATA_URL)

        if response.ok:
            iss_data = xmltodict.parse(response.content)
            parsed_iss_data = parse_iss_data(iss_data)
            
            # Store data in redis db
            r.set("iss_data", json.dumps(parsed_iss_data))
            logger.info(f"Loaded state vectors into redis db.")
            return parsed_iss_data
        else:
            logging.error(f"Failed to fetch ISS data: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching ISS data: {e}", exc_info=True)
        return None

def parse_iss_data(xml_data: dict) -> List[Dict[str, Any]]:
    """
    Parse the ISS data and store as a list of dicts.

    Args:
        xml_data (dict): Parsed XML data in dict.

    Returns:
        List[Dict[str, Any]]: List of dicts.
    """
    parsed_iss_data = []

    try:
        # Extract data based on xml structure
        state_vectors = (
            xml_data.get("ndm", {})
            .get("oem", {})
            .get("body", {})
            .get("segment", {})
            .get("data", {})
            .get("stateVector", [])
        )

        # Handle empty data
        if not state_vectors:
            raise ValueError("No state vectors found in XML data.")

        # Convert data to list of dicts
        for state_vector in state_vectors:
            try:
                data_point = {
                    "EPOCH": state_vector.get("EPOCH", ""),
                    "X": float(state_vector.get("X", {}).get("#text", 0)),
                    "Y": float(state_vector.get("Y", {}).get("#text", 0)),
                    "Z": float(state_vector.get("Z", {}).get("#text", 0)),
                    "X_DOT": float(state_vector.get("X_DOT", {}).get("#text", 0)),
                    "Y_DOT": float(state_vector.get("Y_DOT", {}).get("#text", 0)),
                    "Z_DOT": float(state_vector.get("Z_DOT", {}).get("#text", 0)),
                }
                parsed_iss_data.append(data_point)

            except ValueError as ve:
                logging.error(f"ValueError parsing state vector: {state_vector} - {ve}")

        return parsed_iss_data

    except Exception as e:
        logging.error(f"Error parsing ISS data: {e}")
        return []

def get_iss_data_cached() -> List[Dict[str, Any]]:
    """
    Retrieve cached ISS data from Redis. If not available, fetch from the ISS data.

    Args:
        None

    Returns:
        iss_data (List[Dict[str, Any]]): A list of ISS data dictionaries if available.
    """
    data = r.get("iss_data")
    if data:
        logger.info("ISS data loaded from redis db.")
        return json.loads(data)
    logger.info("No ISS data found in redis db, fetching from ISS")
    return fetch_iss_data()

def get_time_range(iss_data: List[Dict[str, Any]]) -> Tuple[datetime, datetime]:
    """
    Calculate the range of data using timestamps from the first and last epochs.

    Args:
        iss_data (List[Dict[str, Any]]): List of dicts containing ISS data.
    
    Returns:
        Tuple[datetime, datetime]: A tuple with the first and last timestamps.
    """
    first_epoch = iss_data[0]["EPOCH"]
    last_epoch = iss_data[-1]["EPOCH"]

    # Formate to readable datetime
    time_format = "%Y-%jT%H:%M:%S.%fZ"
    first_time = datetime.strptime(first_epoch, time_format)
    last_time = datetime.strptime(last_epoch, time_format)

    return first_time, last_time

def get_closest_data_point(iss_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find the closest data point to the current time in UTC time zone.

    Args:
        iss_data (List[Dict[str, Any]): List of dicts from ISS data.

    Returns:
        Dict[str, Any]: Dict of the closest data point.
    """
    # Get current UTC time
    now = datetime.now(timezone.utc)

    # Create a copy (lambda) of the original list before sorting
    sorted_data = sorted(iss_data, key=lambda x: abs(now - parser.isoparse(x["EPOCH"])))

    return sorted_data[0]

def cal_average_speed(iss_data: List[Dict[str, Any]]) -> float:
    """
    Calculates the average speed over the ISS data set.

    Args:
        iss_data (List[Dict[str, Any]]): List of dicts of ISS data.

    Returns:
        float: Average speed.
    """
    try:
        total_speed = 0.0
        for data_point in iss_data:
            # add up all speed
            total_speed += (data_point["X_DOT"]**2 + data_point["Y_DOT"]**2 + data_point["Z_DOT"]**2)**0.5

        # cal avg speed
        return total_speed / len(iss_data) if iss_data else 0.0

    except Exception as e:
        logging.error(f"Error calculating speed: {e}")
        return 0.0

def cal_instantaneous_speed(epoch_data: List[Dict[str, Any]]) -> float:
    """
    Calculate instantaneous speed for a specific Epoch.
    Args:
        epoch_data (List[Dict[str, Any]]): List of the epoch.

    Returns:
        float: Instantaneous speed.
    """
    speed = (
        float(epoch_data["X_DOT"])**2 +
        float(epoch_data["Y_DOT"])**2 +
        float(epoch_data["Z_DOT"])**2
    )**0.5
    return speed

# Return entire data set
@app.route('/epochs', methods=['GET'])
def get_epochs():
    data = get_iss_data_cached()

    if data:
        return jsonify(data)
    return jsonify({"error": "Failed to fetch ISS data"}), 500

# Return modified list of Epochs given query parameters
@app.route('/epochs', methods=['GET'])
def get_modified_epochs_list():
    try:
        # Get limit and offset from query parameters
        limit = int(request.args.get('limit', default=5))  # default limit is 5   
        offset = int(request.args.get('offset', default=0))  # default offset is 0  

        if limit < 0 or offset < 0:
            raise ValueError("limit and offset must be non-negative integers")

        data = get_iss_data_cached()

        if data:
            result = data[offset:offset + limit]
            return jsonify(result)
    
    except ValueError as ve:
        return jsonify({"error": "Invalid value for limit or offset", "details": str(ve)}), 400

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Return state vectors for a specific Epoch from the data set
@app.route('/epochs/<epoch>', methods=['GET'])
def get_state_vectors_for_epoch(epoch: str):
    try:
        parsed_iss_data = get_iss_data_cached()

        if parsed_iss_data:
            epoch_data = [data for data in parsed_iss_data if data["EPOCH"] == epoch]
            if epoch_data:
                return jsonify(epoch_data)
        return jsonify({"error": f"No data found for the specified epoch: {epoch}"}), 404

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Route to get instantaneous speed for a specific Epoch in the data set
@app.route('/epochs/<epoch>/speed', methods=['GET'])
def get_instantaneous_speed_for_epoch(epoch: str):
    try:
        parsed_iss_data = get_iss_data_cached()

        if parsed_iss_data:
            epoch_data = [data for data in parsed_iss_data if data["EPOCH"] == epoch]
            if epoch_data:
                speed = cal_instantaneous_speed(epoch_data[0])
                return jsonify({"instantaneous_speed": speed})
            return jsonify({"error": f"No data found for the specified epoch: {epoch}"}), 404

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Return latitude, longitude, altitude, and geoposition for a specific Epoch in the data set
@app.route('/epochs/<epoch>/location', methods=['GET'])
def get_epoch_location(epoch):
    data = get_iss_data_cached()

    state = next((s for s in data if s.get("epoch") == epoch), None)

    if state is None:
        return jsonify({"error": "Epoch not found"}), 404

    position = state.get("position", {})
    x, y, z = position.get("x", 0), position.get("y", 0), position.get("z", 0)
    
    xy_sqrt = math.sqrt(x**2 + y**2)
    latitude = math.degrees(math.atan2(z, xy_sqrt))
    longitude = math.degrees(math.atan2(y, x))
    altitude = math.sqrt(x**2 + y**2 + z**2) - 6371  # Earth's radius in km

    geolocator = Nominatim(user_agent="iss_tracker")
    
    try:
        location = geolocator.reverse((latitude, longitude), language="en", exactly_one=True)
        geoposition = location.address if location else "Unknown"
    except Exception as e:
        print(f"Geolocation error: {e}")
        geoposition = "Unknown"

    return jsonify({
        "epoch": epoch,
        "latitude": latitude,
        "longitude": longitude,
        "altitude_km": altitude,
        "geoposition": geoposition
    })

# Route to get state vectors and instantaneous speed for the Epoch that is nearest in time
@app.route('/now', methods=['GET'])
def get_nearest_epoch():
    try:
        parsed_iss_data = fetch_iss_data()

        if parsed_iss_data:
            # Find the closest data point to 'now'
            closest_data_point = get_closest_data_point(parsed_iss_data)

            # Calculate and include instantaneous speed closest to 'now'
            closest_data_point["instantaneous_speed"] = cal_instantaneous_speed(closest_data_point)

            return jsonify(closest_data_point)
        return jsonify({"error": "Failed to fetch ISS data"}), 500

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)