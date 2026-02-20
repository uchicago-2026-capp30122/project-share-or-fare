import argparse
from .join import join_api_csv
from .make_csv import clean, group_rides, format_for_api, sample_and_split

####### CHANGE THESE PARAMETERS ###############################################

# Note: When we run join on our full dataset the relationship between transit
#       data and rideshare data is one to many, but for this example we are
#       using one to one data.
#       For now, we can use the merged dataset to run exploratory data analysis

#### 1. Set file names
# MAKE CSV:
# Set this to the full path to the raw data file
RAW_DATA_PATH = ""

# JOIN:
# Set the name for the transit data file, api response file, and the intended
# output file name.
# All files are CSV files in project-share-or-fare/data
RIDESHARE_DATA = "sabrina_500"
API_DATA = "sabrina_500_api_response"
OUTPUT_NAME = "sabrina_500_merged"

#### 2. Run `uv run python -m rideshare --join` from project-share-or-fare
#       directory

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

    if args.makecsv >= 0:
        size = args.makecsv
        data = clean(RAW_DATA_PATH)
        unique_rides = group_rides(data)
        unique_rides_formatted = format_for_api(unique_rides)

        print(f"Making csv files for {size} unique API calls")
        sample_and_split(unique_rides_formatted, size)

    if args.join:
        rideshare_transit_data = join_api_csv(RIDESHARE_DATA, API_DATA)
        rideshare_transit_data.to_csv(f"./data/{OUTPUT_NAME}.csv", index=False)


if __name__ == "__main__":
    main()
