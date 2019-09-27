import random
import string

import pytest


@pytest.fixture(scope="class")
def token():
    return ''.join(random.choice(string.hexdigits) for _ in range(15))


@pytest.fixture()
def login_response(token):
    login_response = f"""
        {{
            "token": "{token}",
            "language": "es"
        }}
        """
    return login_response


@pytest.fixture()
def user_id():
    return ''.join(random.choice(string.hexdigits) for _ in range(24))


@pytest.fixture()
def auth_user_id_response(user_id):
    auth_user_id_response = f"""
        {{
            "_id": "{user_id}",
            "holidayDates": [
                "2019-04-19T00:00:00.000Z",
                "2019-08-19T00:00:00.000Z",
                "2019-09-19T00:00:00.000Z"
            ]
        }}
    """
    return auth_user_id_response


@pytest.fixture()
def absences_response():
    absences_response = """
        {
    "skip": 0,
    "limit": 50,
    "count": 2,
    "totalCount": 2,
    "data": [
        {
            "_id": "esfsa",
            "start": "2019-08-10T00:00:00.000Z",
            "end": "2019-08-19T00:00:00.000Z"
        },
        {
            "_id": "asdad",
            "start": "2019-08-19T00:00:00.000Z",
            "end": "2019-09-02T00:00:00.000Z"
        }
    ]
}
    """
    return absences_response
