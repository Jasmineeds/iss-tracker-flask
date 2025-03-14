import pytest
from datetime import datetime
from iss_tracker import (
    parse_iss_data,
    get_time_range,
    get_closest_data_point,
    cal_average_speed
)

@pytest.fixture
def sample_xml_data():
    return {
        "ndm": {
            "oem": {
                "body": {
                    "segment": {
                        "data": {
                            "stateVector": [ 
                                
                                {'EPOCH': '2025-058T11:53:00.000Z', 'X': {'@units': 'km', '#text': '2674.73145218746'}, 'Y': {'@units': 'km', '#text': '3316.2289606109498'}, 'Z': {'@units': 'km', '#text': '-5297.4214788776399'}, 'X_DOT': {'@units': 'km/s', '#text': '-5.3196592851300499'}, 'Y_DOT': {'@units': 'km/s', '#text': '5.4534040548973604'}, 'Z_DOT': {'@units': 'km/s', '#text': '0.73246350063873'}}, 
                                
                                {'EPOCH': '2025-058T11:57:00.000Z', 'X': {'@units': 'km', '#text': '1316.58492360587'}, 'Y': {'@units': 'km', '#text': '4489.0743177531904'}, 'Z': {'@units': 'km', '#text': '-4931.3291171098199'}, 'X_DOT': {'@units': 'km/s', '#text': '-5.9294790985872803'}, 'Y_DOT': {'@units': 'km/s', '#text': '4.2606771881374801'}, 'Z_DOT': {'@units': 'km/s', '#text': '2.2999334681557699'}}, 
                                
                                {'EPOCH': '2025-058T12:00:00.000Z', 'X': {'@units': 'km', '#text': '229.643996617211'}, 'Y': {'@units': 'km', '#text': '5158.9603929330797'}, 'Z': {'@units': 'km', '#text': '-4419.0464244079003'}, 'X_DOT': {'@units': 'km/s', '#text': '-6.1063351683023903'}, 'Y_DOT': {'@units': 'km/s', '#text': '3.1568493905097599'}, 'Z_DOT': {'@units': 'km/s', '#text': '3.37272993036005'}}
                            ]
                        }
                    }
                }
            }
        }
    }

@pytest.fixture
def sample_iss_data():
    return [
        {
            'EPOCH': '2025-058T11:53:00.000Z',
            'X': 2674.73145218746,
            'Y': 3316.2289606109498,
            'Z': -5297.4214788776399,
            'X_DOT': -5.3196592851300499,
            'Y_DOT': 5.4534040548973604,
            'Z_DOT': 0.73246350063873
        },
        {
            'EPOCH': '2025-058T11:57:00.000Z',
            'X': 1316.58492360587,
            'Y': 4489.07431775319,
            'Z': -4931.32911710982,
            'X_DOT': -5.92947909858728,
            'Y_DOT': 4.26067718813748,
            'Z_DOT': 2.29993346815577
        },
        {
            'EPOCH': '2025-058T12:00:00.000Z',
            'X': 229.643996617211,
            'Y': 5158.96039293308,
            'Z': -4419.0464244079,
            'X_DOT': -6.10633516830239,
            'Y_DOT': 3.15684939050976,
            'Z_DOT': 3.37272993036005
        }
    ]

def test_parse_iss_data(sample_xml_data):
    parsed_iss_data = parse_iss_data(sample_xml_data)
    assert len(parsed_iss_data) == 3
    assert parsed_iss_data[0]["EPOCH"] == "2025-058T11:53:00.000Z"
    assert parsed_iss_data[1]["X"] == 1316.58492360587
    assert parsed_iss_data[2]["X_DOT"] == -6.10633516830239

def test_get_time_range(sample_iss_data):
    time_range = get_time_range(sample_iss_data)
    # datetime object
    expected_start = datetime(2025, 2, 27, 11, 53, 0)
    expected_end = datetime(2025, 2, 27, 12, 0, 0)

    assert time_range == (expected_start, expected_end)

def test_get_closest_data_point(sample_iss_data):
    closest_data_point = get_closest_data_point(sample_iss_data)

    assert closest_data_point["EPOCH"] == "2025-058T11:53:00.000Z"

def test_cal_average_speed(sample_iss_data):
    avg_speed = cal_average_speed(sample_iss_data)
    expected_avg_speed = 7.6551
    tolerance = 0.5

    assert abs(avg_speed - expected_avg_speed) <= tolerance

if __name__ == '__main__':
    # Run tests: pytest
    pytest.main(['-v'])
