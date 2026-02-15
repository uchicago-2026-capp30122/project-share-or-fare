# cached_get.py
import httpx
import time
from datetime import datetime
from pathlib import Path
import os



# GLOBALS
API_KEY = os.environ["API_KEY"] # DO NOT change this line!
CACHE_DIR = Path(__file__).parent / "_cache"
URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


class FetchException(Exception):
    """
    Turn a httpx.Response into an exception.
    """

    def __init__(self, response: httpx.Response):
        super().__init__(
            f"{response.status_code} retrieving {response.url}: {response.text}"
        )

def get_json_request_params(origin: tuple[str,str], destination: tuple[str,str], 
                            year: str, month:str, day: str, hour: str) -> tuple[dict,dict]:
    """
    Provide a string tuple of origin and destination (latitude, longitude) and returns
    the header and data object needed for the API call. 

    Parameters:
    - origin and destination (latitude, longitude) tuples
    - year: 4 digit string (ex. "2026")
    - month: 2 digit string (ex. "02")
    - day: 2 digit string (ex. "29")
    - hour: 2 digit string, in 24-hour format (ex. "14"). Must be UTC!

    Returns:
    - Header and data dictionary object for http.request
    """
    origin_lat, origin_long = origin
    dest_lat, dest_long = destination

    # Constructing timestamp object
    date_str = f"{year}-{month}-{day}T{hour}:{00}:00Z"


    headers = {"Content-Type": "application/json", 
             "X-Goog-Api-Key": API_KEY,
             "X-Goog-FieldMask": "routes.legs.steps.travelMode,routes.legs.steps.staticDuration,routes.legs.steps.distanceMeters,routes.legs.steps.transitDetails.transitLine.vehicle.type,routes.legs.steps.transitDetails,routes.distanceMeters,routes.duration"}
            #  "X-Goog-FieldMask": "routes.localizedValues.distance,routes.localizedValues.duration,routes.localizedValues.transitFare,routes.polyline,routes.legs.steps.travelMode"}
                            
    data = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin_lat,
                    "longitude": origin_long
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": dest_lat,
                    "longitude": dest_long
                }
            }
        },
        "travelMode": "TRANSIT",
        "departureTime": date_str,
        "computeAlternativeRoutes": False,
        "languageCode": "en-US",
        "units": "IMPERIAL"
    }
    return headers, data


def cached_get(origin: tuple[str,str], destination: tuple[str,str], 
               year: str, month:str, day: str, hour: str, id: str) -> str:
    """
    Retrieves the response text from the cache using the Trip ID if it exists,
    otherwise makes another API call and caches that result.
    
    """

    # If CACHE_DIR does not exist, create it
    if not CACHE_DIR.exists():
        print("Created _cache directory")
        CACHE_DIR.mkdir()

    # If cache key already exists in CACHE_DIR, return that that response
    cache_key_path = CACHE_DIR / id
    if cache_key_path.exists():
        with open(cache_key_path, "r") as f:
            cached_response = f.read()
        print("Returning cached response")
        return cached_response
    
    # Otherwise, make the API call and store response in CACHE_DIR
    else:
        time.sleep(0.5)
        headers, data = get_json_request_params(origin, destination, year, 
                                                month, day, hour)
        print(f"Making API call for {id}")
        response = httpx.post(URL, follow_redirects=True, 
                              headers = headers,
                              json = data)
        if response.status_code == 200:
            with open(cache_key_path, "w") as f:
                f.write(response.text)
            return response.text
        else:
            raise FetchException(response)