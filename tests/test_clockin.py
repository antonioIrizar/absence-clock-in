from datetime import datetime

import pytest
import httpretty
from httpretty.core import HTTPrettyRequest

from clockin import Absence


class TestClockIn(object):
    @pytest.fixture()
    def login(self, login_response):
        def request_callback(request: HTTPrettyRequest, uri: str, response_headers: dict) -> list:
            content_type = request.headers.get('Content-Type')
            assert content_type == 'application/json', 'Unexpected content type'
            return [200, response_headers, login_response]

        httpretty.enable()
        httpretty.register_uri(httpretty.POST, Absence.BASE_URL + '/auth/login', body=request_callback)

    @pytest.fixture()
    def timespans_create(self, token):
        def request_callback(request: HTTPrettyRequest, uri: str, response_headers: dict) -> list:
            content_type = request.headers.get('Content-Type')
            x_vacationtoken = request.headers.get('x-vacationtoken')
            assert request.parsed_body['timezone'] == '+0000', 'Incorrect timezone'
            assert datetime.strptime(request.parsed_body['start'], '%Y-%m-%dT%H:%M:%SZ')
            assert datetime.strptime(request.parsed_body['start'], '%Y-%m-%dT%H:%M:%SZ')
            assert content_type == 'application/json', 'Unexpected content type'
            assert x_vacationtoken == token, 'Invalid token for authentication'
            return [200, response_headers, ""]

        httpretty.enable()
        httpretty.register_uri(httpretty.POST, Absence.BASE_URL + '/v2/timespans/create', body=request_callback)

    def test_get_token(self, login, token):
        absence = Absence()
        assert absence.token == token, 'Token is not correct'

    def test_create_register(self, login, timespans_create):
        absence = Absence()
        start = datetime.now()
        end = datetime.now()
        absence.create_register(start, end)
