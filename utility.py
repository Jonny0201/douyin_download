from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from requests.exceptions import ReadTimeout, ConnectionError, ChunkedEncodingError
import os
import re
import requests
import atexit
import time

def get_chrome(configure) :
    def quit_driver(driver) :
        try :
            driver.quit()
        except :
            pass
    basic_path = os.path.dirname(os.path.abspath(__file__))
    if configure["path"]["basic"] != "" :
        basic_path = configure["path"]["basic"]
    data_path = os.path.join(basic_path, str(configure["path"]["cookies"]).lstrip("/\\"))
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={data_path}")
    options.set_capability("goog:loggingPrefs", {"performance" : "ALL"})
    options.set_capability("goog:chromeOptions", {
        "perfLoggingPrefs": {
            "enableNetwork": True,
            "enablePage": True
        }
    })
    driver = webdriver.Chrome(
        service = Service(ChromeDriverManager().install()),
        options = options
    )
    driver.execute_cdp_cmd("Network.enable", {})
    atexit.register(quit_driver, driver)
    return driver
def normalize_url(url) :
    result = re.search(r'^(https?://[^/]+/(?:video|note)/\d+)', url)
    return result.group(1) if result else ""
def request(url, *, timeout = (10, 3600), retries = 3, backoff_s = 1.0) :
    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Not A;Brand";v="99", "Chromium";v="145", "Google Chrome";v="145"',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.iesdouyin.com/share/video/6561991332561161476/?region=CN&mid=6561671254439365390&u_code=0&titleType=title&did=MS4wLjABAAAA2Cy8LTQsppRk4gci9RcF18kdcuNyaQRtZcZt0BGbylg&iid=MS4wLjABAAAAWHQavP6vURszBFMcxNrThBB0wrNEDWNzLdTKiuW5cI_cOJvn7h0u20Uz8R292pd2&with_sec_did=1&utm_source=copy_link&utm_campaign=client_share&utm_medium=android&app=aweme&scheme_type=1',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cookie': 'MONITOR_WEB_ID=4843f090-b627-46db-bbe2-f757b4ea21a0; _tea_utm_cache_1243={%22utm_source%22:%22copy_link%22%2C%22utm_medium%22:%22android%22%2C%22utm_campaign%22:%22client_share%22}'
    }
    s = requests.Session()
    s.trust_env = False
    last_exc = None
    for attempt in range(max(1, int(retries))) :
        try :
            resp = s.get(url, headers = headers, verify = False, timeout = timeout, stream = True)
            return resp
        except (ReadTimeout, ConnectionError, ChunkedEncodingError) as e :
            last_exc = e
            if attempt < max(1, int(retries)) - 1 :
                sleep_s = backoff_s * (2 ** attempt)
                time.sleep(sleep_s)
            else :
                raise
        except Exception as e :
            raise
    raise last_exc
def path_add(lhs, rhs) :
    return os.path.join(lhs, str(rhs).lstrip("/\\"))