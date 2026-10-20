from unittest.mock import patch


@patch("requests.get")
def test_fetch_users(mock_get):
    mock_get.return_value.json.return_value = [{"id": 1}]
    users = fetch_users()
    assert len(users) == 1
