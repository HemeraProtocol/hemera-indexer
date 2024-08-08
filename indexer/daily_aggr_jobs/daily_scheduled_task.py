"""
This is a sample timer scheduler.
"""
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def create_session(url):
    Session = sessionmaker(bind=(create_engine(url)))
    session = Session()
    return session


def get_yesterday_date():
    now = datetime.now()

    yesterday_datetime = now - timedelta(days=1)

    today_str = now.strftime('%Y-%m-%d')
    yesterday_str = yesterday_datetime.strftime('%Y-%m-%d')

    return today_str, yesterday_str


def get_sql_content(path):
    end_date_str, start_date_str = get_yesterday_date()

    f = open(path, 'r')
    sql_template = f.read()
    sql = sql_template.format(yesterday=start_date_str, today=end_date_str)
    return sql


pg_url = "your pg url"
session = create_session(pg_url)

daily_wallet_addresses_aggregates_sql = get_sql_content('./daily_wallet_addresses_aggregates.sql')

session.execute(text(daily_wallet_addresses_aggregates_sql))

period_wallet_addresses_aggregates_sql = get_sql_content('./period_wallet_addresses_aggregates.sql')

session.execute(text(period_wallet_addresses_aggregates_sql))
