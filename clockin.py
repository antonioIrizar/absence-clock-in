import calendar
import json
import os
import random
import urllib.request
import urllib.error
from datetime import datetime, timedelta, date

EMAIL = os.environ['ABSENCE_EMAIL']
PASSWORD = os.environ['ABSENCE_PASS']


class Absence:
    BASE_URL = 'https://app.absence.io/api'
    WORKDAY_WORKTIME: timedelta = timedelta(hours=8, minutes=15)
    TIME_TO_EAT = timedelta(hours=1)
    MAX_TIME: timedelta = timedelta(hours=6)
    REDUCED_WORKTIME: timedelta = timedelta(hours=7)

    def __init__(self, year, month, day=None):
        self.email = EMAIL
        self.password = PASSWORD
        self.token = self.get_token()
        self._auth_response = self._get_auth_response()
        self.year = year
        self.month = month
        self.day = day
        self.holidays = set()
        self.holidays.update(self.get_national_holidays())
        self.holidays.update(self.get_holidays())

    def get_token(self) -> str:
        data = {
            'email': self.email,
            'password': self.password,
            'company': None,
            'trace': []
        }

        body = json.dumps(data).encode('utf8')
        req = urllib.request.Request(f'{self.BASE_URL}/auth/login',
                                     data=body,
                                     headers={'content-type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            response = json.loads(response.read())
            token = response['token']

        return token

    def _get_auth_response(self) -> dict:
        req = urllib.request.Request(f'{self.BASE_URL}/auth/{self.token}',
                                     headers={'content-type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            response = json.loads(response.read())

        return response

    @property
    def user_id(self):
        return self._auth_response['_id']

    def get_national_holidays(self):
        first_day_of_month = date(self.year, self.month, 1)
        end_day_of_month = date(self.year, self.month, self.max_day_of_month)
        national_holidays = []
        for holiday in self._auth_response['holidayDates']:
            holiday_date = self.string_to_date(holiday)
            if holiday_date < first_day_of_month:
                continue
            elif holiday_date > end_day_of_month:
                break
            national_holidays.append(holiday_date)

        return national_holidays

    def create_register(self, start: datetime, end: datetime):
        if start.date() in self.holidays:
            return False

        data = {
            'userId': self.user_id,
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
        req = urllib.request.Request(f'{self.BASE_URL}/v2/timespans/create',
                                     data=body,
                                     headers={'content-type': 'application/json', 'x-vacationtoken': self.token})

        try:
            with urllib.request.urlopen(req):
                pass
        except urllib.error.URLError as e:
            message = e.read().decode('utf-8')
            if e.code == 412 and message == 'Los registros no se pueden solapar':
                print(f'Day {self.day} has register hours')
                return False
            else:
                print(f'Error code {e.code} with message {message}')
                raise
        return True

    @property
    def workday(self) -> date:
        return datetime(year=self.year, month=self.month, day=self.day).date()

    @property
    def is_friday(self) -> bool:
        return self.workday.weekday() == 4

    @property
    def is_summertime(self) -> bool:
        return self.workday.month in (7, 8)

    @property
    def is_reduced_workday(self) -> bool:
        return self.is_friday or self.is_summertime

    @property
    def morning_hours(self) -> list:
        if self.is_reduced_workday:
            return [8]

        return [8, 9]

    @property
    def mealtime_hours(self) -> list:
        return [13, 14, 15]

    @property
    def minutes(self) -> list:
        return [0, 10, 20, 30, 40, 50]

    @property
    def max_day_of_month(self) -> int:
        return calendar.monthrange(self.year, self.month)[1]

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
        return mealtime_end + self.WORKDAY_WORKTIME - time_work_on_morning

    @staticmethod
    def string_to_date(date_on_string) -> date:
        return datetime.strptime(date_on_string[:-5], '%Y-%m-%dT%H:%M:%S').date()

    def get_holidays(self):
        data = {
            'filter': {
                'assignedToId': self.user_id,
                'status': {'$in': [2]},
                'start': {
                    '$gte': f'{self.year}-{self.month}-01'
                }
            },
            'sortBy': {
                'start': 1
            }
        }

        body = json.dumps(data).encode('utf8')
        req = urllib.request.Request(f'{self.BASE_URL}/v2/absences',
                                     data=body,
                                     headers={'content-type': 'application/json', 'x-vacationtoken': self.token})
        with urllib.request.urlopen(req) as response:
            response = json.loads(response.read())
            holidays = []
            for holiday_data in response['data']:
                start = self.string_to_date(holiday_data['start'])
                if start.month != self.month:
                    break
                end = self.string_to_date(holiday_data['end'])
                if start.month != end.month:
                    end_day = self.max_day_of_month + 1
                else:
                    end_day = end.day
                for day in range(start.day, end_day):
                    holidays.append(date(self.year, self.month, day))
        return holidays


class ClockIn:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.absence = Absence(year, month)

    def _weekday_no_friday(self):
        entry_time = self.absence.get_entry_time()
        mealtime_start = self.absence.get_mealtime_start(entry_time)
        mealtime_end = mealtime_start + self.absence.TIME_TO_EAT
        time_work_on_morning = mealtime_start - entry_time
        departure_time = self.absence.get_departure_time(mealtime_end, time_work_on_morning)

        self.absence.create_register(entry_time, mealtime_start)
        self.absence.create_register(mealtime_end, departure_time)

    def _reduced_day(self):
        entry_time = self.absence.get_entry_time()
        departure_time = entry_time + self.absence.REDUCED_WORKTIME

        self.absence.create_register(entry_time, departure_time)

    def one_day(self, day: int):
        self.absence.day = day

        if self.absence.workday not in self.absence.holidays:
            self._reduced_day() if self.absence.is_reduced_workday else self._weekday_no_friday()
        else:
            print(f'You was on holiday at {self.absence.workday}')

    def one_month(self):
        for day in range(1, self.absence.max_day_of_month + 1):
            if datetime(year=self.year, month=self.month, day=day).weekday() < 5:
                self.one_day(day)
