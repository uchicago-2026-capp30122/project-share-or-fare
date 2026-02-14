from cached_get import cached_get
from parse_response import parse_response
import json
from pathlib import Path
import os
import csv

####### CHANGE THESE PARAMETERS ###############################################
#### 1. Set API Key
# To set API KEY environment variable: export API_KEY=<key>
# To check: echo $API_KEY
API_KEY = os.environ["API_KEY"] # DO NOT change this line!

#### 2. Enter your name and dataset size
# This will be used for the input and output file names
NAME = "sarah"
SIZE = "500"

###############################################################################

# Define input and output files
INPUT_FILE = Path(__file__).parent.parent / "data" / f"{NAME}_{SIZE}.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / f"{NAME}_{SIZE}_api_response.csv"



def make_api_response_csv(input_file, output_file):
    # Read in input file
    with open(input_file, "r") as input:
        reader = csv.DictReader(input)
        out_list = []
        for row in reader:

            # Extract necessary data from row
            origin_lat = row["Pickup Centroid Latitude"]
            origin_long = row["Pickup Centroid Longitude"]
            dest_lat = row["Dropoff Centroid Latitude"]
            dest_long = row["Dropoff Centroid Longitude"]
            year = "todo"
            month = "todo"
            day = "todo"
            hour = "todo"
            
            # Makes API call or pulls from cache to get raw response
            response_text = cached_get((origin_lat, origin_long),
                                       (dest_lat, dest_long),
                                       year, month, day, hour)

            # Process the response into a dictionary
            response_dict = parse_response(response_text)

            # Add group id (key for matching)
            response_dict["group_id"] = row["group_id"]

            out_list.append(response_dict)

    # Write to output csv
    fieldnames = ["group_id", "walkDist_meters", "walkTime_s", 
                  "transitDist_meters", "transitTime_s",
                  "totalDist_meters", "totalTime_s", "modes"]
    with open(output_file, "w",newline="") as output:
        writer = csv.DictWriter(output, fieldnames = fieldnames)
        for dict in out_list:
            writer.writerow(dict)



if __name__ == "__main__":
    make_api_response_csv(INPUT_FILE, OUTPUT_FILE)