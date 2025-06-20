import requests
import json
import time
def bangumi_request(search_payload, offset):
    API_URL = f"https://api.bgm.tv/v0/search/subjects?offset={offset}&limit=20"
    ACCESS_TOKEN = ""  # 从 https://bgm.tv/settings/tokens 获取
    headers = {
        "User-Agent": "foxabbage/foxabbage.github.io",
        "Content-Type": "application/json"
    }
    try:
        # 发送POST请求
        response = requests.post(
            API_URL,
            headers=headers,
            data=json.dumps(search_payload)  # 注意使用json.dumps转换
        )

        # 检查响应状态
        if response.status_code == 200:
            results = response.json()
            total = results['total']
            name_id = {}

            # 打印搜索结果
            for item in results["data"]:
                if item['name_cn'] != None and item['name_cn'] != '':
                    name_id[item['name_cn']] = item['id']
                else:
                    name_id[item['name']] = item['id']
            return total, name_id
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")


def bangumi_request_all(search_payload, total):
    offset = 0
    n = (total - 1) // 20 + 1
    name_id = {}
    for i in range(n):
        total, name_id_temp = bangumi_request(search_payload, offset)
        name_id.update(name_id_temp)
        time.sleep(1)
        offset += 20
    return name_id