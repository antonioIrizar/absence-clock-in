from datetime import datetime, date
from unittest import mock

import pytest
import httpretty
from httpretty.core import HTTPrettyRequest

from clockin import Absence, ClockIn


class TestAbsence(object):
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

    def test_workday(self):
        year = 2021
        month = 2
        day = 3
        absence = Absence(year=year, month=month, day=day)

        assert absence.workday == datetime(year=year, month=month, day=day).date()

    @pytest.mark.parametrize('day,expected', [
        (11, False),
        (12, True)
    ])
    def test_is_friday(self, day, expected):
        absence = Absence(year=2021, month=2, day=day)

        assert absence.is_friday == expected

    @pytest.mark.parametrize(
        'month,expected',
        [(month, month in (7, 8)) for month in range(1, 13)])
    def test_is_summertime(self, month, expected):
        absence = Absence(year=2021, month=month, day=1)

        assert absence.is_summertime == expected

    @pytest.mark.parametrize('register_date,expected', [
        (datetime(year=2021, month=2, day=12).date(), True),  # Friday
        (datetime(year=2021, month=8, day=1).date(), True),  # Summertime not friday
        (datetime(year=2021, month=2, day=11).date(), False),  # Normal day
    ])
    def test_is_reduced_workday(self, register_date, expected):
        absence = Absence(year=register_date.year, month=register_date.month, day=register_date.day)

        assert absence.is_reduced_workday is expected


class TestClockIn(object):

    def test_create_friday_register(self):
        clock_in = ClockIn(2021, 2)

        with mock.patch('clockin.ClockIn._reduced_day') as mock_create_register:
            clock_in.one_day(12)

        mock_create_register.assert_called()

    def test_create_weekday_no_friday_register(self):
        clock_in = ClockIn(2021, 2)

        with mock.patch('clockin.ClockIn._weekday_no_friday') as mock_create_register:
            clock_in.one_day(11)

        mock_create_register.assert_called()

    def test_create_register_in_summertime(self):
        clock_in = ClockIn(2021, 8)

        with mock.patch('clockin.ClockIn._reduced_day') as mock_create_register:
            clock_in.one_day(1)

        mock_create_register.assert_called()
