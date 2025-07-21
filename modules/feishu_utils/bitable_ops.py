import requests
from pathlib import Path
import yaml
from loguru import logger
import random
import json
import math
from modules.feishu_utils.bitable_record import BitableRecord


HEADERS = {
    "Content-Type": "application/json; charset=utf-8"
}


# 飞书应用凭证配置
class FeishuConfig:
    # APP_ID = "your_app_id"
    # APP_SECRET = "your_app_secret"
    # BITABLE_APP_TOKEN = "your_bitable_app_token"
    # BITABLE_TABLE_ID = "your_table_id"

    @staticmethod
    def _get_app_credential():
        local_config_path = Path(__file__).parent.parent.parent / "configs" / "configs.yaml"

        with open(local_config_path, "r") as f:
            config = yaml.safe_load(f)

        app_id = config["Feishu"]["app_id"]
        app_secret = config["Feishu"]["app_secret"]

        return app_id, app_secret

    APP_ID, APP_SECRET = _get_app_credential()


def get_tenant_access_token():
    api_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    headers = HEADERS

    data = {
        "app_id": FeishuConfig.APP_ID,
        "app_secret": FeishuConfig.APP_SECRET,
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=data
    )

    return f"Bearer {response.json()['tenant_access_token']}"


def get_wiki_app_token(app_token: str):
    api_url = "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    params = {
        "token": "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    }

    response = requests.get(
        api_url,
        headers=headers,
        params=params
    )

    try:
        wiki_app_token = response.json()["data"]["node"]["obj_token"]

        return wiki_app_token
    except KeyError:
        return response.json()


def get_tables(app_token: str):
    api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    response = requests.get(
        api_url,
        headers=headers
    )

    return response.json()


def get_record(app_token: str, table_id: str, view_id: str, filter_item: dict):
    api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    # params = {
    #     'page_token': '',
    #     'page_size': 500,
    # }

    data = {
        'automatic_fields': False,
        'view_id': view_id,
        'filter': filter_item,
    }

    # response = requests.post(api_url, headers=headers, params=params, json=data)
    response = requests.post(
        api_url,
        headers=headers,
        json=data
    )

    try:
        return response.json()['data']['items']
    except KeyError:
        return response.json()

def get_records(app_token: str, table_id: str, view_id: str, filter_item: dict = None):
    api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    params = {
        'page_token': '',
        'page_size': 500,
    }

    data = {
        'automatic_fields': False,
        'view_id': view_id,
        'filter': filter_item,
    }

    responses = []

    while True:
        response = requests.post(
            api_url,
            headers=headers,
            params=params,
            json=data,
            timeout=10
        )
        # print(response.json())
        page_token = response.json().get('data').get('page_token')

        responses.extend(response.json()['data']['items'])

        if not page_token:
            break

        params['page_token'] = page_token

    return [BitableRecord(record_item) for record_item in responses]

def get_record_ids(app_token: str, table_id: str, view_id: str, filter_item: dict = None):
    records = get_records(app_token, table_id, view_id, filter_item)

    return [record["record_id"] for record in records]

def get_records_by_id(app_token: str, table_id: str, record_ids):
    api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_get"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    data = {
        'record_ids': record_ids,
        'automatic_fields': False,
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=data
    )

    try:
        # return response.json()['data']['records'][0]['fields']
        return response.json()['data']['records'][0]
    except KeyError:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return response.text


def insert_record(app_token: str, table_id: str, fields: dict):
    api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    data = {
        'fields': fields,
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=data
    )

    return response.json()

def update_records(app_token: str, table_id: str, records: list[dict]):
    api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    total_records = len(records)
    batch_size = 1000
    batch_num = math.ceil(len(records) / batch_size)

    for batch_index in range(batch_num):
        start_idx = batch_index * batch_size
        end_idx = min(start_idx + batch_size, total_records)
        batch_records = records[start_idx:end_idx]

        data = {
            'records': batch_records,
        }

        response = requests.post(api_url, headers=headers, json=data)

        if response.json()['code'] == 0:
            logger.success(f"{len(batch_records)} records updated successfully")
        else:
            logger.error(f"\n{json.dumps(response.json(), indent=4, ensure_ascii=False)}")

def delete_records(app_token: str, table_id: str, record_ids: list[str]):
    api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete"

    headers = {
        "Authorization": get_tenant_access_token(),
    } | HEADERS

    total_ids = len(record_ids)
    batch_size = 500
    batch_num = math.ceil(len(record_ids) / batch_size)

    for batch_index in range(batch_num):
        start_idx = batch_index * batch_size
        end_idx = min(start_idx + batch_size, total_ids)
        batch_ids = record_ids[start_idx:end_idx]

        data = {
            'records': batch_ids,
        }

        response = requests.post(api_url, headers=headers, json=data)

        if response.json()['code'] == 0:
            logger.success(f"{len(batch_ids)} records deleted successfully")
        else:
            logger.error(f"\n{json.dumps(response.json(), indent=4, ensure_ascii=False)}")


if __name__ == "__main__":
    app_token = get_wiki_app_token()
    app_token = "EkLqbaVqIaKM0Rs2wTacJk2SnAc"
    table_id = "tbl5Ga8Rzp2vPpwu"
    view_id = "vew7Pzllde"

    print(json.dumps(get_records(), indent=4, ensure_ascii=False))
    # print(get_records()['data']['items'])
    # print(len(get_records()['data']['items']))

    # print(get_record_by_id(['recuMofhYkUb9y']))