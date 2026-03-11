import argparse
from .join import join_api_csv, join_neighborhood_data
from .make_csv import (
    clean,
    group_rides,
    format_for_api,
    get_month_ride_groups,
    sample_and_split,
)
from .clean_route_data import clean_route_data, prep_data_for_map
import pandas as pd

########################## CHANGE THESE PARAMETERS #############################


#### MAKE CSVS OF SAMPLE DATA FOR API CALL INPUT: ####
# 1. Set file name
# Set this to your full local path to the raw data file.
# This is the file download from chicago data portal with all rideshare rides
# in 2025
RAW_DATA_PATH = "~/Downloads/tnp.csv"

# 2. Run the command
# The command will sample from the dataset [n * 4] unique rows, then create
# and store 4 equal sized CSV files, n rows each, one under each group
# member's name, in the data directory.
#
# Run the following command, replacing n with the number of rows
#   `uv run python -m data_processing --makecsv n`
#
# For example, for 10k rows, run
#   `uv run python -m data_processing --makecsv 10000`

# 3. Output
# This process should output:
#   - 4 files formatted to call with the api process, for example
#       "./data/molly_10k.csv"
#       "./data/sabrina_10k.csv"
#       "./data/sarah_10k.csv"
#       "./data/waleed_10k.csv"
#   - "" --  a file with unique trips by month, used for joining api data back
#       into our individual trip level data


#### JOIN RIDESHARE, TRANSIT, NEIGHBORHOOD DATA: ####
# 1. Set file name
# Set the name for the api response file, neighborhood data file, and the
# intended output file name.
# All files are CSV files in project-share-or-fare/data
RIDESHARE_DATA = "ride_groups"
NEIGHBORHOOD_DATA = "data/Neighborhoods_2012b_20260227.csv"

# 2. Run the dataset
# From project-share-or-fare directory run:
#   `uv run python -m data_processing --join`

# 3. Output
# This process should ouput
#   - "/data/rideshare_transit_data.csv" -- a file containing individual trips
#       with rideshare and transit data
#   - "./data/neighborhood_route_data.csv" -- a file containing unique trips
#       grouped by start and end neighborhood with rideshare data, transit data,
#       and neighborhood polygons


###############################################################################


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--makecsv",
        type=int,
        help="Clean raw CSV and store one portion for every group member",
    )
    parser.add_argument(
        "--join", action="store_true", help="Join transit data into rideshare data"
    )
    args = parser.parse_args()

    # Make CSV
    # Runs the code to load, clean, sample, and split our data into the
    # desired size and writes to a csv for each group member (4 csvs total)
    if args.makecsv and args.makecsv >= 0:
        size = args.makecsv
        data = clean(RAW_DATA_PATH)
        unique_rides = group_rides(data)
        unique_rides_formatted = format_for_api(data, unique_rides)

        print(f"Writing csv files for {size} unique API calls")
        sample_and_split(unique_rides_formatted, size)
        print("Success")

        month_groups = get_month_ride_groups(data)
        print("Writing month_ride_group dataset to 'data/ride_groups.csv'")
        month_groups.to_csv("../data/ride_groups.csv", index=False)
        print(f"Success, agregated data has {len(month_groups)} rows")

    # Join
    # Runs the code to join our transit api responses back into our initial
    # rideshare dataset
    if args.join:
        rideshare_transit_data = join_api_csv(RIDESHARE_DATA)

        # Add in pickup and dropoff neighborhood names
        neighborhood_boundaries = pd.read_csv(NEIGHBORHOOD_DATA)
        rideshare_transit_data_neighborhoods = join_neighborhood_data(
            rideshare_transit_data, neighborhood_boundaries
        )  # Takes 2-3 hours

        # Some minor cleaning
        # (adding transitPenalty variable, reformatting fields)
        rideshare_transit_data_neighborhoods_clean = clean_route_data(
            rideshare_transit_data_neighborhoods
        )

        # Output disaggregated data set for data visualization
        rideshare_transit_data_neighborhoods_clean.to_csv(
            "./data/rideshare_transit_data.csv", index=False
        )

        # Output neighborhood-level dataset for map
        neighborhood_route_data = prep_data_for_map(
            rideshare_transit_data_neighborhoods_clean, neighborhood_boundaries
        )

        neighborhood_route_data.to_csv(
            "./data/neighborhood_route_data.csv", index=False
        )


if __name__ == "__main__":
    main()
