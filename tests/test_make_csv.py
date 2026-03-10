import pytest
import pandas as pd
import io
import data_processing.make_csv as mc


def test_clean():
    # Row 1: Valid Chicago trip
    # Row 2: Invalid (90% Chicago) - should be dropped
    csv_data = """Trip ID,Trip Start Timestamp,Trip End Timestamp,Trip Seconds,Trip Miles,Percent Time Chicago,Percent Distance Chicago,Pickup Census Tract,Dropoff Census Tract,Fare,Tip,Additional Charges,Trip Total,Pickup Centroid Latitude,Pickup Centroid Longitude,Dropoff Centroid Latitude,Dropoff Centroid Longitude
A,05/01/2025 10:00:00 AM,05/01/2025 10:10:00 AM,600,2.0,100%,100%,1,2,10,2,1,13,41.8,-87.6,41.8,-87.6
B,05/01/2025 11:00:00 AM,05/01/2025 11:10:00 AM,600,2.0,90%,100%,1,2,10,2,1,13,41.8,-87.6,41.8,-87.6
    """
    df = mc.clean(io.StringIO(csv_data))

    assert len(df) == 1
    assert df.iloc[0]["Trip ID"] == "A"
    # Ensure timezone conversion to UTC worked (Central Time + 5 hours in May)
    assert df.iloc[0]["Trip Start Timestamp"].hour == 15


def test_group_rides():
    # Two trips with very close coordinates that should round to 41.878 and -87.629
    # One is a Thursday (Day 0), one is a Saturday (Day 1)
    # Using UTC to avoid local time shifts during the test
    data = pd.DataFrame(
        {
            "Trip Start Timestamp": [
                pd.Timestamp("2025-05-01 10:00:00", tz="UTC"),  # Thursday
                pd.Timestamp("2025-05-01 10:45:00", tz="UTC"),  # Thursday (same hour)
                pd.Timestamp("2025-05-03 10:00:00", tz="UTC"),  # Saturday
            ],
            "Pickup Centroid Latitude": [41.8781, 41.8784, 41.8781],
            "Pickup Centroid Longitude": [-87.6291, -87.6294, -87.6291],
            "Dropoff Centroid Latitude": [41.880, 41.880, 41.880],
            "Dropoff Centroid Longitude": [-87.630, -87.630, -87.630],
        }
    )

    unique_calls = mc.group_rides(data)

    # The two Thursday trips should be 1 group, the Saturday trip should be its own group.
    assert len(unique_calls) == 2
    # Find the group with the two trips
    weekday_group = unique_calls[unique_calls["day_type"] == 0]
    assert weekday_group["group_n"].iloc[0] == 2


def test_format_for_api():
    # Mocking the two inputs the function expects
    unique_calls = pd.DataFrame({"day_type": [0, 1, 2]})
    data = pd.DataFrame({"day_type": [0, 1, 2]})

    result = mc.format_for_api(data, unique_calls)

    # Check 0 -> 22, 1 -> 25, 2 -> 26
    assert result.loc[result["day_type"] == 0, "representative_day"].iloc[0] == 22
    assert result.loc[result["day_type"] == 1, "representative_day"].iloc[0] == 25
    assert result.loc[result["day_type"] == 2, "representative_day"].iloc[0] == 26
    assert result["representative_year"].unique()[0] == "2026"
