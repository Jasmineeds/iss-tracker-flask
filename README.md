# ISS Tracker with Flask and Redis

## Overview
This project is a Flask-based API that tracks the International Space Station (ISS) using real-time data. The application stores ISS positional data in a Redis database and provides multiple routes to retrieve information about the ISS’s location and speed.

## Features
- Retrieves ISS position data from an external API.
- Stores ISS data in a Redis container for persistence.
- Provides RESTful API endpoints to fetch ISS speed, position, and historical data.
- Containerized with Docker and orchestrated using Docker Compose.

## Setup and Deployment

### Prerequisites
- Docker and Docker Compose installed.

### Installation & Running
1. Clone this repository:
   ```sh
   git clone <repo-url>
   cd iss-tracker
   ```
2. Build and start the application using Docker Compose:
   ```sh
   docker-compose up --build
   ```
3. The Flask API will be available at `http://localhost:5000`.

## API Endpoints

### 1. Get all epochs
```sh
curl http://localhost:5000/epochs
```
Returns all available epochs from the dataset.

### 2. Get a specific epoch
```sh
curl http://localhost:5000/epochs/<epoch>
```
Returns state vectors for the given epoch.

### 3. Get speed for a specific epoch
```sh
curl http://localhost:5000/epochs/<epoch>/speed
```
Returns the instantaneous speed of the ISS at the given epoch.

### 4. Get location for a specific epoch
```sh
curl http://localhost:5000/epochs/<epoch>/location
```
Returns latitude, longitude, altitude, and geolocation for the given epoch.

### 5. Get current ISS location
```sh
curl http://localhost:5000/now
```
Returns the current position, altitude, and speed of the ISS.

## Running Tests
To run the unit tests inside the container:
```sh
docker exec flask_container pytest
```

## Data Source
ISS data is retrieved from [Open Notify](http://api.open-notify.org/iss-now.json).

## Diagram
A software architecture diagram (`diagram.png`) is included in this repository, illustrating how the Flask app, Redis, and external API interact.

## License
This project follows standard open-source licensing practices.
