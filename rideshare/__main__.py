import argparse
from .join import join_api_csv

####### CHANGE THESE PARAMETERS ###############################################

# Note: When we run this on our full dataset the relationship between transit
#       data and rideshare data is one to many, but for this example we are
#       using one to one data.
#       For now, we can use the merged dataset to run exploratory data analysis

#### 1. Set file names
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
        "--makecsv", action="store_true", help="Clean raw CSV"
    )
    parser.add_argument(
        "--join", action="store_true", help="Join transit data into rideshare data"
    )
    args = parser.parse_args()

    if args.makecsv:
        pass

    if args.join:
        rideshare_transit_data = join_api_csv(RIDESHARE_DATA, API_DATA)
        rideshare_transit_data.to_csv(f"./data/{OUTPUT_NAME}.csv", index=False)


if __name__ == "__main__":
    main()
