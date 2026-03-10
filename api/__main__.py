from .cached_get import cached_get
from .parse_response import parse_response
import json
from pathlib import Path
import csv

####### CHANGE THESE PARAMETERS ###############################################
#### 1. Set API Key
# To set API KEY environment variable: export API_KEY=<key>
# To check: echo $API_KEY

#### 2. Enter your name and dataset size
# This will be used for the input and output file names
# file should be in root/data
# Make sure to save this file before running
NAME = "waleed"
SIZE = "10k"

#### 3. Run <uv run python -m api> from project-share-or-fare directory

###############################################################################

# Define input and output files
INPUT_FILE = Path(__file__).parent.parent / "data" / f"{NAME}_{SIZE}.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / f"{NAME}_{SIZE}_api_response.csv"


def make_api_response_csv(input_file, output_file):
    # Read in input file
    with open(input_file, "r") as input:
        reader = csv.DictReader(input)
        out_list = []
        for i, row in enumerate(reader):
            # Extract necessary data from row
            origin_lat = row["Pickup Centroid Latitude"]
            origin_long = row["Pickup Centroid Longitude"]
            dest_lat = row["Dropoff Centroid Latitude"]
            dest_long = row["Dropoff Centroid Longitude"]
            year = row["representative_year"]
            month = row["representative_month"]
            day = row["representative_day"]
            hour = row["start_hour"]
            group_id = row["group_id"]

            # Makes API call or pulls from cache to get raw response
            response_text = cached_get(
                (origin_lat, origin_long),
                (dest_lat, dest_long),
                year,
                month,
                day,
                hour,
                group_id,
            )

            # Process the response into a dictionary
            response_dict = parse_response(response_text)

            # Add group id (key for matching)
            response_dict["group_id"] = group_id
            print(f"Rows processed: {i + 1}")
            out_list.append(response_dict)

    # Write to output csv
    fieldnames = [
        "group_id",
        "walkDist",
        "walkTime",
        "transitDist",
        "transitTime",
        "totalDist",
        "totalTime",
        "modes",
    ]
    with open(output_file, "w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, restval="")
        writer.writeheader()
        for dict in out_list:
            writer.writerow(dict)
    print(f"Output {output_file}")


if __name__ == "__main__":
    make_api_response_csv(INPUT_FILE, OUTPUT_FILE)
