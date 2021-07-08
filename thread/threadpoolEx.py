# coding: utf-8
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
from requests import adapters

from proxy import get_proxies

headers = {
    "Host": "splcgk.court.gov.cn",
    "Origin": "https://splcgk.court.gov.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Referer": "https://splcgk.court.gov.cn/gzfwww/ktgg",
}
url = "https://splcgk.court.gov.cn/gzfwww/ktgglist?pageNo=1"

def spider(page):
    data = {
        "bt": "",
        "fydw": "",
        "pageNum": page,
    }
    for _ in range(5):
        try:
            response = requests.post(url, headers=headers, data=data, proxies=get_proxies())
            json_data = response.json()
        except (json.JSONDecodeError, adapters.SSLError):
            continue
        else:
            break
    else:
        return {}

    return json_data

def main():
    with ThreadPoolExecutor(max_workers=8) as t:
        obj_list = []
        begin = time.time()
        for page in range(1, 15):
            obj = t.submit(spider, page)
            obj_list.append(obj)

        for future in as_completed(obj_list):
            data = future.result()
            print(data)
            print('*' * 50)
        times = time.time() - begin
        print(times)

if __name__ == "__main__":
    main()
