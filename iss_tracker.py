import logging
from datetime import datetime, timezone
from dateutil import parser
from flask import Flask, request, jsonify

import requests
import xmltodict

from typing import Any, Dict, List, Tuple, Optional

ISS_DATA_URL = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"

app = Flask(__name__)

def setup_logging():
    logging.basicConfig(
        filename="iss_tracker.log",
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

setup_logging()

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
    try:
        # GET request to ISS data URL
        response = requests.get(url='https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')

        # Check if status code 2XX
        if response.ok:
            # Parse the XML content and convert into a dict
            iss_data = xmltodict.parse(response.content)

            # Extract state vector information
            parsed_iss_data = parse_iss_data(iss_data)

            # Return the entire data set as JSON format
            return jsonify(parsed_iss_data)

        else:
            # Return an error message if the request fails
            return jsonify({"error": "Failed to fetch data"}), 500

    except Exception as e:
        # Log any errors
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Return modified list of Epochs given query parameters
@app.route('/epochs', methods=['GET'])
def get_modified_epochs_list():
    try:
        # Get limit and offset from query parameters
        limit = int(request.args.get('limit', default=5))  # default limit is 5   
        offset = int(request.args.get('offset', default=0))  # default offset is 0  

        if limit < 0 or offset < 0:
            raise ValueError("limit and offset must be non-negative integers")

        response = requests.get(url='https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')
        
        if response.ok:
            iss_data = xmltodict.parse(response.content)
            parsed_iss_data = parse_iss_data(iss_data)

            # Pagination
            modified_data = parsed_iss_data[offset:offset + limit]

            return jsonify(modified_data)
        else:
            return jsonify({"error": f"Failed to fetch ISS data."}), 500
    
    except ValueError as ve:
        return jsonify({"error": "Invalid value for limit or offset", "details": str(ve)}), 400

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Return state vectors for a specific Epoch from the data set
@app.route('/epochs/<epoch>', methods=['GET'])
def get_state_vectors_for_epoch(epoch: str):
    try:
        response = requests.get(url='https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')

        if response.ok:
            iss_data = xmltodict.parse(response.content)
            parsed_iss_data = parse_iss_data(iss_data)

            # Find data for the specified epoch
            epoch_data = [data_point for data_point in parsed_iss_data if data_point["EPOCH"] == epoch]
            
            if epoch_data:
                return jsonify(epoch_data)
            else:
                return jsonify({"error": f"No data found for the specified epoch: {epoch}"}), 404
        else:
            return jsonify({"error": f"Failed to fetch ISS data."}), 500

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Route to get instantaneous speed for a specific Epoch in the data set
@app.route('/epochs/<epoch>/speed', methods=['GET'])
def get_instantaneous_speed_for_epoch(epoch: str):
    try:
        response = requests.get(url='https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')

        if response.ok:
            iss_data = xmltodict.parse(response.content)
            parsed_iss_data = parse_iss_data(iss_data)

            # Find data for the specified epoch
            epoch_data = [data_point for data_point in parsed_iss_data if data_point["EPOCH"] == epoch]

            if epoch_data:
                # Cal instantaneous speed for the specified epoch
                speed = cal_instantaneous_speed(epoch_data[0])
                return jsonify({"instantaneous_speed": speed})
            else:
                return jsonify({"error": f"No data found for the specified epoch: {epoch}"}), 404
        else:
            return jsonify({"error": "Failed to fetch ISS data."}), 500

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Route to get state vectors and instantaneous speed for the Epoch that is nearest in time
@app.route('/now', methods=['GET'])
def get_nearest_epoch():
    try:
        response = requests.get(url='https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')

        if response.ok:
            iss_data = xmltodict.parse(response.content)
            parsed_iss_data = parse_iss_data(iss_data)

            # Find the closest data point to 'now'
            closest_data_point = get_closest_data_point(parsed_iss_data)

            # Calculate and include instantaneous speed closest to 'now'
            closest_data_point["instantaneous_speed"] = cal_instantaneous_speed(closest_data_point)

            return jsonify(closest_data_point)
        else:
            return jsonify({"error": "Failed to fetch ISS data."}), 500

    except Exception as e:
        logging.error("Unexpected error occurred", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)