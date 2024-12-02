import json
import logging
from datetime import datetime, timedelta
import yaml

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 定义错误日志文件路径
# 定义 Feishu API 的基础 URL 和端点
feishu_base_url = "https://open.larksuite.com/open-apis"
im_endpoint = "/im/v1/messages"
token_endpoint = "/auth/v3/app_access_token/internal"


def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


import os

config_path = os.path.join(os.path.dirname(__file__), "config/config.yaml")
config = load_config(config_path)

# 使用示例
# config = load_config("app/config/config.yaml")
app = config.get("app")
pg_urls = config.get("database").get('pg_urls')
app_id = app.get("app_id")
app_secret = app.get("app_secret")
receive_id = app.get("receive_id")
user_id = app.get("user_id")
user_name = app.get("user_name")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_access_token():
    auth_url = f"{feishu_base_url}{token_endpoint}"
    auth_payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    auth_headers = {
        'Content-Type': 'application/json'
    }
    auth_response = requests.post(auth_url, json=auth_payload, headers=auth_headers)
    auth_data = auth_response.json()
    return auth_data.get('app_access_token')


def send_message(access_token, content, error=False):
    url = f"{feishu_base_url}{im_endpoint}"

    params = {"receive_id_type": "chat_id"}

    content_format = "<at user_id=\"%s\">%s</at> %s"
    if error:
        message_request_content = content_format % (user_id, user_name, content)
        content = message_request_content

    req = {
        "receive_id": receive_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }

    payload = json.dumps(req)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, params=params, headers=headers, data=payload)

    print(response.headers['X-Tt-Logid'])  # 用于调试或紧急处理
    print(response.content)  # 打印响应


def fbtc_alarm(chain_name, is_yesterday):
    yesterday_str, today_str = get_yesterday_date()

    if is_yesterday:
        start_date = yesterday_str
    else:
        start_date = today_str

    logging.info(f'Executing scheduled job for date: {start_date}')

    pg_url = pg_urls.get(chain_name)
    Session = sessionmaker(bind=(create_engine(pg_url)))
    session = Session()
    protocol_sql = 'select protocol_id, total_fbtc_balance, total_fbtc_usd, total_user_count from period_feature_defi_fbtc_aggregates where period_date = :start_date order by total_fbtc_balance desc'
    protocol_results = session.execute(text(protocol_sql), {'start_date': start_date}).all()

    states_sql = """ select count(1) as holders, sum(total_fbtc_balance)  as total_fbtc_balance, max(total_fbtc_balance) as max_total_fbtc_balance, max(update_time) as update_time  from period_feature_defi_wallet_fbtc_detail where period_date = :start_date"""
    states_results = session.execute(text(states_sql), {'start_date': start_date}).fetchone()

    session.close()

    access_token = get_access_token()
    if not protocol_results and not states_results:
        content = f'Missing data for {start_date}'
        # 发送消息
        send_message(access_token, f"FBTC DAILY ALARM!!! \n CHAIN NAME: {chain_name}\n{content}", True)
    else:
        holders = states_results.holders
        total_fbtc_balance = states_results.total_fbtc_balance
        max_total_fbtc_balance = states_results.max_total_fbtc_balance
        update_time = states_results.update_time

        alert_message = (
            f"CHAIN NAME: {chain_name}\n"
            f"DATE: {start_date}\n"
            f"The number of holders is {holders},\n"
            f"With a total fBTC balance of {total_fbtc_balance}.\n"
            f"The maximum recorded fBTC balance is {max_total_fbtc_balance}.\n"
            f"The updated time is {update_time}.\n"
        )
        if protocol_results:
            columns = ['protocol_id', 'total_fbtc_balance', 'total_fbtc_usd', 'total_user_count']
            data = [columns] + protocol_results  # 包括列名在内

            # 格式化每一行，使用 "| " 作为分隔符
            formatted_rows = ["  ".join(map(str, row)) for row in data]

            # 合并为完整内容
            content = "\n".join(formatted_rows)
        else:
            content = "with no protocols"
        alert_message += f"\n{content}"
        send_message(access_token, f"FBTC DAILY Result!!!\n"
                                   f"{alert_message}")


def cmeth_alarm(chain_name, is_yesterday):
    yesterday_str, today_str = get_yesterday_date()

    if is_yesterday:
        start_date = yesterday_str
    else:
        start_date = today_str

    logging.info(f'Executing scheduled job for date: {start_date}')

    pg_url = pg_urls.get(chain_name)
    Session = sessionmaker(bind=(create_engine(pg_url)))
    session = Session()
    protocol_sql = 'select protocol_id, total_cmeth_balance, total_cmeth_usd, total_user_count from period_feature_defi_cmeth_aggregates where period_date = :start_date order by total_cmeth_balance desc'
    protocol_results = session.execute(text(protocol_sql), {'start_date': start_date}).all()

    states_sql = """ select count(1) as holders, sum(total_cmeth_balance)  as total_cmeth_balance, max(total_cmeth_balance) as max_total_cmeth_balance, max(update_time) as update_time  from period_feature_defi_wallet_cmeth_detail where period_date = :start_date"""
    states_results = session.execute(text(states_sql), {'start_date': start_date}).fetchone()

    session.close()

    access_token = get_access_token()
    if not protocol_results and not states_results:
        content = f'Missing data for {start_date}'
        # 发送消息
        send_message(access_token, f"cmETH DAILY ALARM!!! \n CHAIN NAME: {chain_name}\n{content}", True)
    else:
        holders = states_results.holders
        total_cmeth_balance = states_results.total_cmeth_balance
        max_total_cmeth_balance = states_results.max_total_cmeth_balance
        update_time = states_results.update_time

        alert_message = (
            f"CHAIN NAME: {chain_name}\n"
            f"DATE: {start_date}\n"
            f"The number of holders is {holders},\n"
            f"With a total fBTC balance of {total_cmeth_balance}.\n"
            f"The maximum recorded fBTC balance is {max_total_cmeth_balance}.\n"
            f"The updated time is {update_time}.\n"
        )
        if protocol_results:
            columns = ['protocol_id', 'total_cmeth_balance', 'total_cmeth_usd', 'total_user_count']
            data = [columns] + protocol_results  # 包括列名在内

            # 格式化每一行，使用 "| " 作为分隔符
            formatted_rows = ["  ".join(map(str, row)) for row in data]

            # 合并为完整内容
            content = "\n".join(formatted_rows)
        else:
            content = "with no protocols"
        alert_message += f"\n{content}"
        send_message(access_token, f"cmETH DAILY Result!!!\n"
                                   f"{alert_message}")


def schedule_jobs(is_yesterday=True):
    # chain_name_list = ['eth', 'mantle', 'bsc']
    # # chain_name_list = ['bsc']
    # # start_date = '2024-09-23'  # 替换为你的动态日期
    # for chain_name in chain_name_list:
    #     fbtc_alarm(chain_name, is_yesterday)
    fbtc_alarm('mantle', is_yesterday)
    cmeth_alarm('mantle', is_yesterday)
    fbtc_alarm('eth', is_yesterday)
    cmeth_alarm('eth', is_yesterday)
    fbtc_alarm('bsc', is_yesterday)
    fbtc_alarm('bob', is_yesterday)
    fbtc_alarm('arbitrum', is_yesterday)


def get_yesterday_date():
    now = datetime.now()

    yesterday_datetime = now - timedelta(days=1)

    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = yesterday_datetime.strftime("%Y-%m-%d")

    return yesterday_str, today_str


if __name__ == '__main__':
    # fbtc_alarm('mantle', True)
    # schedule_jobs()

    print('----- START Monitor -----')
    logging.info(f'START Monitor')

    scheduler = BlockingScheduler()

    yesterday_str, today_str = get_yesterday_date()

    # 在每天 2 点执行
    scheduler.add_job(schedule_jobs, 'cron', hour=2, minute=0, args=(True,))

    trigger = CronTrigger.from_crontab("0 7,13,19 * * *")
    scheduler.add_job(schedule_jobs, trigger=trigger, args=(False,))

    scheduler.start()  # 启动调度器
