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
