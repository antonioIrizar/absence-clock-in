import random
import string

import pytest


@pytest.fixture()
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
            "_id": "{user_id}"
        }}
    """
    return auth_user_id_response