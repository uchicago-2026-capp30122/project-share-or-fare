import pytest
import pandas as pd
from unittest.mock import patch
from dashboard.visualization.transform import (
    log_transform_time,
    dataset_sample,
    weighted_median,
    get_text,
)


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "Count": [1, 2],
            "rideshareTime": [10, 100],
            "totalTransitTime": [12, 18],
            "Average Trip Seconds": [120, 134],
            "transitPenalty": [100, 2.1],
        }
    )


def test_log_transform_time_add_cols(df):
    transformed_df = log_transform_time(df)
    assert len(transformed_df.columns) == 7


def test_log_transform_time_rideshare_values(df):
    transformed_df = log_transform_time(df)
    assert transformed_df["Log Rideshare Min"].tolist() == [1.0, 2.0]


def test_log_transform_time_transit_values(df):
    transformed_df = log_transform_time(df)
    assert transformed_df["Log Transit Min"].tolist() == [1.0, 1.2]


@patch("dashboard.visualization.transform.random.randint", return_value=0)
def test_dataset_sample_tens_includes(_, df):
    sample_df = dataset_sample(df, 10)
    assert sample_df["Average Trip Seconds"].iloc[0] == 120


@patch("dashboard.visualization.transform.random.randint", return_value=2)
def test_dataset_sample_tens_not_includes(_, df):
    sample_df = dataset_sample(df, 10)
    assert len(sample_df) == 0


@patch("dashboard.visualization.transform.random.randint", return_value=20)
def test_dataset_sample_hundreds_includes(_, df):
    sample_df = dataset_sample(df, 100)
    assert sample_df["Average Trip Seconds"].iloc[0] == 120


@patch("dashboard.visualization.transform.random.randint", return_value=65)
def test_dataset_sample_hundreds_not_includes(_, df):
    sample_df = dataset_sample(df, 100)
    assert len(sample_df) == 0


@patch("dashboard.visualization.transform.random.randint", return_value=4)
def test_dataset_sample_remove_long_trips(_, df):
    sample_df = dataset_sample(df, 10)
    assert len(sample_df) == 0


def test_weighted_median_mini(df):
    weighted_median(df, "transitPenalty") == 2.1


def test_get_text_ordinary():
    expected_result = "This test file contains this text"
    assert get_text("tests/test_files/test.txt") == expected_result


def test_get_text_bad_filepath():
    assert get_text("tests/test_files/no_file.txt") == ""
