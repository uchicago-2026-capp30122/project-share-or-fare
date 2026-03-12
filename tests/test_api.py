from pathlib import Path

import pytest

from api.parse_response import parse_response

TEST_FILES = Path(__file__).parent.parent / "tests/test_files"


# Dummy response data (replaced with random values)
@pytest.fixture
def sample_response_no_transit():
    f = open(TEST_FILES / "sample_response_no_transit.txt")
    resp = f.read()
    f.close()
    return resp


@pytest.fixture
def sample_response_w_transit():
    f = open(TEST_FILES / "sample_response_w_transit.txt")
    resp = f.read()
    f.close()
    return resp


def test_parse_response_empty():
    assert parse_response("{}") == {}


def test_parse_response_correct_length_no_transit(sample_response_no_transit):
    assert len(parse_response(sample_response_no_transit)) == 7


def test_parse_response_correct_length_w_transit(sample_response_w_transit):
    assert len(parse_response(sample_response_w_transit)) == 7


def test_parse_response_no_transit_dist_time(sample_response_no_transit):
    assert parse_response(sample_response_no_transit)["transitDist"] == 0
    assert parse_response(sample_response_no_transit)["transitTime"] == 0

    assert parse_response(sample_response_no_transit)["walkDist"] == 600
    assert parse_response(sample_response_no_transit)["walkTime"] == 720


def test_parse_response_w_transit_dist_time(sample_response_w_transit):
    assert parse_response(sample_response_w_transit)["transitDist"] == 1000
    assert parse_response(sample_response_w_transit)["transitTime"] == 280

    assert parse_response(sample_response_w_transit)["walkDist"] == 372
    assert parse_response(sample_response_w_transit)["walkTime"] == 559
