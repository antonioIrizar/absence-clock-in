import calendar
import json
import os
import random
import urllib.request
import urllib.error
from datetime import datetime, timedelta

EMAIL = os.environ['ABSENCE_EMAIL']
PASSWORD = os.environ['ABSENCE_PASS']
USER_ID = os.environ['USER_ID']


class Absence:
    BASE_URL = 'https://app.absence.io/api'
    WORKDAY: timedelta = timedelta(hours=8)
    TIME_TO_EAT = timedelta(hours=1)
    MAX_TIME: timedelta = timedelta(hours=6)

    def __init__(self, year=None, month=None, day=None):
        self.email = EMAIL
        self.password = PASSWORD
        self.token = self.get_token()
        self.year = year
        self.month = month
        self.day = day

    def get_token(self) -> str:
        data = {
            'email': self.email,
            'password': self.password,
            'company': None,
            'trace': []
        }

        body = json.dumps(data).encode('utf8')
        req = urllib.request.Request(self.BASE_URL + '/auth/login',
                                     data=body,
                                     headers={'content-type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            response = json.loads(response.read())
            token = response['token']

        return token

    def create_register(self, start: datetime, end: datetime):
        data = {
            'userId': USER_ID,
            '_id': 'new',
            'timezone': '+0000',
            'timezoneName': 'hora de verano de Europa central',
            'type': 'work',
            'commentary': '',
            'start': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end': end.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'trace': []
        }
        body = json.dumps(data).encode('utf8')
        req = urllib.request.Request(self.BASE_URL + '/v2/timespans/create',
                                     data=body,
                                     headers={'content-type': 'application/json', 'x-vacationtoken': self.token})

        try:
            with urllib.request.urlopen(req):
                pass
        except urllib.error.URLError as e:
            message = e.read().decode('utf-8')
            if e.code == 412 and message == 'Los registros no se pueden solapar':
                print(f'Day {self.day} has register hours')
            else:
                print(f'Error code {e.code} with message {message}')
                raise

    @property
    def morning_hours(self) -> list:
        return [8, 9]

    @property
    def mealtime_hours(self) -> list:
        return [13, 14, 15]

    @property
    def minutes(self) -> list:
        return [0, 10, 20, 30, 40, 50]

    def get_random_morning_hour(self) -> int:
        return random.choice(self.morning_hours)

    def get_random_mealtime_hour(self) -> int:
        return random.choice(self.mealtime_hours)

    def get_random_minutes(self) -> int:
        return random.choice(self.minutes)

    def get_entry_time(self) -> datetime:
        return datetime(year=self.year, month=self.month, day=self.day,
                        hour=self.get_random_morning_hour(),
                        minute=self.get_random_minutes())

    def get_mealtime_start(self, entry_time: datetime) -> datetime:
        mealtime_start = datetime(year=self.year, month=self.month, day=self.day,
                                  hour=self.get_random_mealtime_hour(),
                                  minute=self.get_random_minutes())
        if mealtime_start - entry_time > self.MAX_TIME:
            mealtime_start -= (mealtime_start - entry_time) - self.MAX_TIME
        return mealtime_start

    def get_departure_time(self, mealtime_end: datetime, time_work_on_morning: timedelta) -> datetime:
        return mealtime_end + self.WORKDAY - time_work_on_morning


class ClockIn:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.absence = Absence(year, month)

    def one_day(self, day):
        self.absence.day = day
        entry_time = self.absence.get_entry_time()
        mealtime_start = self.absence.get_mealtime_start(entry_time)
        mealtime_end = mealtime_start + self.absence.TIME_TO_EAT
        time_work_on_morning = mealtime_start - entry_time
        departure_time = self.absence.get_departure_time(mealtime_end, time_work_on_morning)

        self.absence.create_register(entry_time, mealtime_start)
        self.absence.create_register(mealtime_end, departure_time)

    def one_month(self):
        for day in range(1, calendar.monthrange(self.year, self.month)[1] + 1):
            if datetime(year=self.year, month=self.month, day=day).weekday() < 5:
                self.one_day(day)
