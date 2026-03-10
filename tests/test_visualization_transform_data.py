import pytest
import pandas as pd
from unittest.mock import patch
from dashboard.visualization.transform import(
    log_transform_time,
    dataset_sample,
    weighted_median,
    get_text
)


@pytest.fixture
def mini_df():
    return pd.DataFrame(
        {
            "Count": [1, 2],
            "rideshareTime": [10, 100],
            "totalTransitTime": [12, 11],
            "Average Trip Seconds": [120, 134],
            "transitPenalty": [100, 2.1],
        }
    )

@patch("dashboard.visualization.transform.random.randint", return_value=4)
def test_dataset_sample_mini(mock_randint, mini_df):
    expected_result = pd.DataFrame(
        {
            "Count": [2],
            "rideshareTime": [100],
            "totalTransitTime": [11],
            "Average Trip Seconds": [134],
            "transitPenalty": [2.1],
        }
    )

    sample_df = dataset_sample(mini_df, 10)
    assert sample_df == expected_result


def test_weighted_median_mini(mini_df):
    weighted_median(mini_df, "transitPenalty") == 2.1


def test_get_text_ordinary():
    expected_result = "This test file contains this text"
    assert get_text("tests/test_files/test.txt") == expected_result


def test_get_text_bad_filepath():
    assert get_text("tests/test_files/no_file.txt") == ""