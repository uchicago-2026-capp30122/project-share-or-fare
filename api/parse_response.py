import json


def parse_response(response_text):
    """
    Takes in response text and reformats into dictionary of:
    {lat: _, long: _, year: _, month: _, day: _, hour: _,
        tripDuration: _, tripDistance: _, tripCost: _}
    """
    input_dict = json.loads(response_text)
    if len(input_dict) == 0:
        return {}
    route_list = input_dict["routes"]
    walking_distance = 0  # in meters
    walking_duration = 0  # in seconds
    transit_distance = 0  # in meters
    transit_duration = 0  # in seconds
    modes = set()

    for route in route_list:
        # route is a dictionary
        for leg in route["legs"]:
            # leg is a dictionary
            for step in leg["steps"]:
                if step["travelMode"] == "WALK":
                    if "distanceMeters" in step.keys():
                        walking_distance += step["distanceMeters"]
                    walking_duration += int(step["staticDuration"][:-1])
                    modes.add("WALK")
                if step["travelMode"] == "TRANSIT":
                    if "distanceMeters" in step.keys():
                        transit_distance += step["distanceMeters"]
                    transit_duration += int(step["staticDuration"][:-1])
                    mode = step["transitDetails"]["transitLine"]["vehicle"]["type"]
                    modes.add(mode)
        total_distance = route["distanceMeters"]
        total_duration = route["duration"]

    return {
        "walkDist": walking_distance,
        "walkTime": walking_duration,
        "transitDist": transit_distance,
        "transitTime": transit_duration,
        "totalDist": total_distance,
        "totalTime": total_duration,
        "modes": modes,
    }
