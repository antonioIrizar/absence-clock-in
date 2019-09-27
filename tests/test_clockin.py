from datetime import datetime, date

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
        httpretty.register_uri(httpretty.POST, f'{Absence.BASE_URL}/auth/login', body=request_callback)

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
        httpretty.register_uri(httpretty.POST, f'{Absence.BASE_URL}/v2/timespans/create', body=request_callback)

    @pytest.fixture()
    def auth_user_id(self, auth_user_id_response, token):
        def request_callback(request: HTTPrettyRequest, uri: str, response_headers: dict) -> list:
            content_type = request.headers.get('Content-Type')
            assert content_type == 'application/json', 'Unexpected content type'
            return [200, response_headers, auth_user_id_response]

        httpretty.enable()
        httpretty.register_uri(httpretty.GET,
                               f'{Absence.BASE_URL}/auth/{token}',
                               body=request_callback)

    @pytest.fixture()
    def absences(self, absences_response, token):
        def request_callback(request: HTTPrettyRequest, uri: str, response_headers: dict) -> list:
            content_type = request.headers.get('Content-Type')
            x_vacationtoken = request.headers.get('x-vacationtoken')
            assert content_type == 'application/json', 'Unexpected content type'
            assert x_vacationtoken == token, 'Invalid token for authentication'
            return [200, response_headers, absences_response]

        httpretty.enable()
        httpretty.register_uri(httpretty.POST, f'{Absence.BASE_URL}/v2/absences', body=request_callback)

    def test_get_token(self, login, auth_user_id, token, absences):
        absence = Absence(2019, 2)
        assert absence.token == token, 'Token is not correct'

    @pytest.mark.parametrize('month,expected', [
        (5, True),
        (8, False)
    ])
    def test_create_register(self, login, auth_user_id, timespans_create, absences, month, expected):
        absence = Absence(2019, month)
        start = datetime(2019, month, 19)
        end = datetime(2019, month, 19, 1)
        assert absence.create_register(start, end) == expected

    def test_get_user_id(self, login, auth_user_id, user_id, absences):
        absence = Absence(2019, 5)
        assert absence.user_id == user_id, 'User id is not correct'

    def test_get_holidays(self, login, auth_user_id, absences):
        absence = Absence(2019, 8)
        holidays = absence.get_holidays()
        for i, day in enumerate(range(10, 31)):
            assert holidays[i] == date(2019, 8, day)

    def test_get_national_holidays(self, login, auth_user_id, absences):
        absence = Absence(2019, 8)
        national_holidays = absence.get_national_holidays()

        assert len(national_holidays) == 1, 'National holidays should only have one day'
        assert national_holidays[0] == date(2019, 8, 19)
