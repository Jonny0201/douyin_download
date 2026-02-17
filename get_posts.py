from selenium.webdriver.common.by import By
import time
import json
import os
import utility

def get_posts(driver, configure, url_list, downloaded_list) :
    try :
        driver.find_element(By.CLASS_NAME, configure["predefined"]["no_posts_tag"])
        print("no posts : " + driver.current_url)
        return []
    except :
        pass
    url_set = set(url_list)
    downloaded_set = set(downloaded_list)
    seen_items = set()
    no_new_steps = 0
    total_steps = 0
    MAX_SCROLL_STEPS = 20000
    STEP_SLEEP = 0.5
    NO_NEW_LIMIT_FOR_CONFIRM = 10 + int(configure["scroll"]["stop_times"])
    for _ in range(MAX_SCROLL_STEPS) :
        if configure["predefined"]["server_exception_tip"] in driver.page_source :
            input("抖音服务异常, 已经暂停, 请手动刷新重试, 建议等待一段时间, 正常后在终端机按下回车")
        total_steps += 1
        moved = driver.execute_script(r"""
            function canScroll(el) {
                if (!el) return false;
                const maxScroll = el.scrollHeight - el.clientHeight;
                if (maxScroll <= 10) return false;
                const before = el.scrollTop;
                el.scrollTop = before + 1;
                const changed = el.scrollTop !== before;
                el.scrollTop = before;
                return changed;
            }
            function pickScrollable(startEl) {
                let el = startEl;
                for (let i = 0; i < 20 && el; ++i) {
                    if (canScroll(el)) return el;
                    el = el.parentElement;
                }
                const doc = document.scrollingElement || document.documentElement;
                if (canScroll(doc)) return doc;
                return doc;
            }
            const list = document.querySelector('[data-e2e="scroll-list"]');
            const start = list || document.querySelector('[data-e2e="user-like-list"]') || document.body;
            const target = pickScrollable(start);
            const before = target.scrollTop;
            target.scrollTop = before + 1200;
            return target.scrollTop !== before;
        """)
        if not moved:
            driver.execute_script(r"""
                function canScroll(el) {
                    if (!el) return false;
                    const maxScroll = el.scrollHeight - el.clientHeight;
                    if (maxScroll <= 10) return false;
                    const before = el.scrollTop;
                    el.scrollTop = before + 1;
                    const changed = el.scrollTop !== before;
                    el.scrollTop = before;
                    return changed;
                }
                function pickScrollable(startEl) {
                    let el = startEl;
                    for (let i = 0; i < 20 && el; ++i) {
                        if (canScroll(el)) return el;
                        el = el.parentElement;
                    }
                    const doc = document.scrollingElement || document.documentElement;
                    if (canScroll(doc)) return doc;
                    return doc;
                }
                const list = document.querySelector('[data-e2e="scroll-list"]');
                const start = list || document.querySelector('[data-e2e="user-like-list"]') || document.body;
                const target = pickScrollable(start);
                target.dispatchEvent(new WheelEvent('wheel', {deltaY: 1200, bubbles: true, cancelable: true}));
                return true;
            """)
        time.sleep(STEP_SLEEP)
        hrefs = driver.execute_script(r"""
            const list = document.querySelector('[data-e2e="scroll-list"]') || document;
            const links = Array.from(list.querySelectorAll('a[href]'));
            function normalizeHref(href) {
                if (!href) return '';
                if (href.startsWith('//')) href = 'https:' + href;
                href = href.split('?')[0].split('#')[0];
                return href;
            }
            const out = new Set();
            for (const a of links) {
                const href = normalizeHref(a.getAttribute('href'));
                if (!href) continue;
                if (href.includes('/video/') || href.includes('/note/')) out.add(href);
            }
            return Array.from(out);
        """)
        before_size = len(seen_items)
        seen_items |= set(hrefs)
        after_size = len(seen_items)
        grew = (after_size != before_size)
        if grew:
            no_new_steps = 0
        else:
            no_new_steps += 1
        if total_steps % 50 == 0 or grew :
            print(f"[scroll] step={total_steps} moved={moved} grew={grew} items={after_size} no_new={no_new_steps}")
        if no_new_steps >= NO_NEW_LIMIT_FOR_CONFIRM :
            if configure["predefined"]["scroll_to_bottom_tip"] in driver.page_source :
                if configure["scroll"]["manually_check"] :
                    if input("请手动确认页面是否已经滑到底部, 已滑到底请在终端机直接回车, 否则输入任意内容后再回车") == "" :
                        break
                else :
                    break
            no_new_steps = 0
        if configure["scroll"]["stop_while_meeting_exists"] :
            stop = False
            for new_url in hrefs :
                if new_url in url_set or new_url in downloaded_set :
                    stop = True
                    break
            if stop :
                break
    seen_items = {item for item in seen_items if item not in url_set and item not in downloaded_set}
    return [
        item if item.startswith("http://") or item.startswith("https://")
        else "https://www.douyin.com" + item
        for item in seen_items
    ]

if __name__ == "__main__" :
    configure = json.load(open("./config.json", 'r', encoding = "utf-8"))
    driver = utility.get_chrome(configure)
    driver.get("https://www.douyin.com")
    input("请将页面定位到想要拉取所有发布作品连结的页面, 例如某个人的个人主页或者你自己的喜欢页面, 确认浏览器载入完毕之后, 在终端机按下回车")
    posts = get_posts(driver, configure, set(), set())
    basic_path = os.path.dirname(os.path.abspath(__file__))
    if configure["path"]["basic"] != "" :
        basic_path = configure["path"]["basic"]
    with open(utility.path_add(basic_path, configure["path"]["url"]), "a+", encoding = "utf-8") as f :
        f.seek(0)
        existing_set = set([line.strip() for line in f.read().splitlines() if line.strip()])
        for url in posts :
            if url in existing_set :
                continue
            f.write(url + "\n")
            existing_set.add(url)