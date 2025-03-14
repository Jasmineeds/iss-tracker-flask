# Homework 05: The Fountains of Flask

This Flask-based API provides access to real-time International Space Station (ISS) position data, parsed from NASA's public XML feed. The API allows querying:

- Retrieve entire ISS data
- Retrieve data for a specific epoch
- Calculate instantaneous speed of a a specific epoch
- Get the closest epoch to the current time

## Project Structure

- `iss_tracker.py`: Reads the XML file and prints summary statistics of the input file.
- `test_iss_tracker.py`: Tests for functions in the main script.
- `Dockerfile`: Docker configuration file for containerization.
- `requirements.txt`: List of Python dependencies.

## Data Source

The dataset contains state vectors describing the ISS's position {X, Y, Z} and velocity {X_DOT, Y_DOT, Z_DOT} over a 15-day period. These vectors use the J2000 reference frame, with Earth as the reference point. The ISS data set is retrieved in real-time from NASA's website. Get the dataset here:

[International Space Station](https://spotthestation.nasa.gov/trajectory_data.cfm)

## Run Scripts

1. Clone the repository
```
git clone https://github.com/Jasmineeds/coe332-jasmine.git
```

2. Navigate to the homework04 directory
```
cd homework05
```

3. Build the Docker Container
```
docker build -t iss-tracker .
```

4. Run the Flask Server
```bash
flask --app iss_tracker --debug run --port=5000
```

The server will start in debug mode on the default port 5000.

## API Endpoints

### Get All Epochs

```
GET /epochs
```

Returns the entire dataset of state vectors for all available time epochs.

**Response Format:**
```json
[
  {
    "EPOCH": "2023-048T12:00:00.000Z",
    "X": 2345.67,
    "Y": 3456.78,
    "Z": 4567.89,
    "X_DOT": 5.67,
    "Y_DOT": 6.78,
    "Z_DOT": 7.89
  },
  ...
]
```

### Get Epochs with Pagination

```
GET /epochs?limit=<int>&offset=<int>
```

Returns a subset of the epochs data with pagination support.

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 5)
- `offset` (optional): Number of records to skip (default: 0)

**Example:**
```
GET /epochs?limit=10&offset=5
```

### Get State Vector for a Specific Epoch

```
GET /epochs/<epoch>
```

Returns the state vector for a specific epoch.

**Example:**
```
GET /epochs/2023-048T12:00:00.000Z
```

**Response Format:**
```json
[
  {
    "EPOCH": "2023-048T12:00:00.000Z",
    "X": 2345.67,
    "Y": 3456.78,
    "Z": 4567.89,
    "X_DOT": 5.67,
    "Y_DOT": 6.78,
    "Z_DOT": 7.89
  }
]
```

### Get Instantaneous Speed for a Specific Epoch

```
GET /epochs/<epoch>/speed
```

Returns the instantaneous speed of the ISS at a specific epoch.

**Example:**
```
GET /epochs/2023-048T12:00:00.000Z/speed
```

**Response Format:**
```json
{
  "instantaneous_speed": 7.82
}
```

### Get Current ISS Data

```
GET /now
```

Returns the state vector and instantaneous speed for the epoch that is nearest to the current time.

**Response Format:**
```json
{
  "EPOCH": "2023-048T12:00:00.000Z",
  "X": 2345.67,
  "Y": 3456.78,
  "Z": 4567.89,
  "X_DOT": 5.67,
  "Y_DOT": 6.78,
  "Z_DOT": 7.89,
  "instantaneous_speed": 7.82
}
```

## Data Model

Each state vector contains the following components:

| Field | Description |
|-------|-------------|
| EPOCH | Timestamp in format YYYY-DDDTHH:MM:SS.sssZ |
| X | X coordinate in km |
| Y | Y coordinate in km |
| Z | Z coordinate in km |
| X_DOT | Velocity in X direction in km/s |
| Y_DOT | Velocity in Y direction in km/s |
| Z_DOT | Velocity in Z direction in km/s |

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid parameters (e.g., negative limit or offset)
- `404 Not Found`: Requested epoch not found
- `500 Internal Server Error`: Server-side errors

## Logging

The application logs errors to `iss_tracker.log` with the following format:
```
YYYY-MM-DD HH:MM:SS - ERROR - Error message
```

## Technical Details

- Built with Flask
- Uses `requests` for HTTP calls
- Uses `xmltodict` for XML parsing
- Uses `dateutil` for date parsing and timezone handling

## Note on Using AI
I used AI to understand the following things:

- How to use jsonify
- How to change the port
- How to create tables in a README file
- The format of status codes