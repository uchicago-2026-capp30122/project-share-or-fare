import pytest
from dashboard.visualization.transform import(
    log_transform_time,
    dataset_sample,
    weighted_median,
    get_text
)

def test_get_text_ordinary():
    expected_result = "This test file contains this text"
    assert get_text("tests/test.txt") == expected_result

def test_get_text_bad_filepath():
    assert get_text("tests/no_file.txt") == ""