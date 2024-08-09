from datetime import datetime, timedelta

import click


def get_yesterday_date():
    now = datetime.now()

    yesterday_datetime = now - timedelta(days=1)

    today_str = now.strftime('%Y-%m-%d')
    yesterday_str = yesterday_datetime.strftime('%Y-%m-%d')

    return today_str, yesterday_str


class DateType(click.ParamType):
    name = "date"

    def convert(self, value, param, ctx):
        try:
            if value is not None:
                datetime.strptime(value, "%Y-%m-%d")
                return value
        except ValueError:
            self.fail(f"{value} is not a valid date in YYYY-MM-DD format", param, ctx)


def check_data_completeness(start_date, end_date):
    return True
