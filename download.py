from selenium.webdriver.common.by import By
import json
import os
import time
import utility
from get_following import save_following
from core import download
from get_posts import get_posts

configure = json.load(open("config.json", "r"))
basic_path = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(utility.path_add(basic_path, configure["path"]["download_path"])) :
    os.makedirs(utility.path_add(basic_path, configure["path"]["download_path"]))
if not os.path.exists(utility.path_add(basic_path, configure["path"]["cookies"])) :
    os.makedirs(utility.path_add(basic_path, configure["path"]["cookies"]))
if not os.path.exists(utility.path_add(basic_path, configure["path"]["tmp"])) :
    os.makedirs(utility.path_add(basic_path, configure["path"]["tmp"]))
driver = utility.get_chrome(configure)
driver.get("https://www.douyin.com")
time.sleep(3)
if (len(driver.find_elements(By.CLASS_NAME, configure["predefined"]["login_tag"])) > 0 or
        len(driver.find_elements(By.ID, "login-panel-new")) > 0 or
        len(driver.find_elements(By.CLASS_NAME, "douyin_login_new_class")) > 0) :
    input("请切换到浏览器页面先登录帐号, 登录完成之后在终端机按下回车")
if configure["path"]["basic"] :
    basic_path = configure["path"]["basic"]
if configure["pull_new_following"] :
    save_following(driver, configure)
pages = list(configure["specific_pages"])
for key in configure["page"] :
    if configure["page"][key] :
        pages.append(configure["predefined"]["url_prefix"] + key)
try :
    with open(utility.path_add(basic_path, configure["path"]["following_users"]), 'r', encoding = "utf-8") as f :
        pages.extend(f.read().splitlines())
except :
    pass
url_list = []
try :
    with open(utility.path_add(basic_path, configure["path"]["url"]), "r+", encoding = "utf-8") as f :
        url_list.extend(f.read().splitlines())
except :
    pass
try :
    with open(utility.path_add(basic_path, configure["path"]["exceptional_url"]), "r+", encoding = "utf-8") as f :
        url_list.extend(f.read().splitlines())
except :
    pass
url_list = set(url_list)
url_list = url_list - set(open(utility.path_add(basic_path, configure["path"]["download_records"]), "r", encoding = "utf-8").read().splitlines())
url_list = list(url_list)
url_list = download(driver, configure, url_list)
pages = set(pages)
pages = pages - set(open(utility.path_add(basic_path, configure["path"]["following_users"])).read().splitlines())
count = len(pages)
for page in pages :
    print("left : " + str(count) + ", url : " + str(len(url_list)))
    driver.get(page)
    new_list = get_posts(driver, configure, url_list, open(utility.path_add(basic_path,
            configure["path"]["download_records"]), "r", encoding = "utf-8").read().splitlines())
    if len(new_list) > 500 :
        print("posts more than 500 : " + page)
    url_list.extend(new_list)
    url_list = download(driver, configure, url_list)
    with open(utility.path_add(basic_path, configure["path"]["url"]), "a+", encoding = "utf-8") as f :
        f.seek(0)
        existing_set = set(f.read().splitlines())
        for url in new_list :
            if url in existing_set :
                continue
            f.write(url + "\n")
            f.flush()
    count -= 1
if len(url_list) > 0 :
    url_list = download(driver, configure, url_list)
    if len(url_list) > 0 :
        with open(utility.path_add(basic_path, configure["path"]["exceptional_url"]), 'w', encoding = "utf-8") as f :
            for url in url_list :
                f.write(url + "\n")
open(utility.path_add(basic_path, configure["path"]["url"]), 'w', encoding = "utf-8").close()