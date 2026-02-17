from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import utility

def save_following(driver, configure) :
    driver.get(configure["predefined"]["my_page"])
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, configure["predefined"]["following_tag"])) ).click()
    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, configure["predefined"]["following_user_tag"])) )
    seen_user_ids = set()
    def collect_user_ids():
        hrefs = driver.execute_script(r"""
            const start = arguments[0];
            const scope = start.closest('[data-e2e="user-fans-container"]') || document;
            const links = Array.from(scope.querySelectorAll('a[href*="/user/"]'));
            function normalizeHref(href){
                if (!href) return '';
                if (href.startsWith('//')) href = 'https:' + href;
                href = href.split('?')[0].split('#')[0];
                return href;
            }
            const ids = new Set();
            for (const a of links) {
                const href = normalizeHref(a.getAttribute('href'));
                if (!href) continue;
                const m = href.match(/\/user\/([^/?#]+)/);
                if (m && m[1]) ids.add(m[1]);
            }
            return Array.from(ids);
        """, element)
        return set(hrefs)
    NO_NEW_LIMIT = 300
    MAX_SCROLL_STEPS = 20000
    STEP_SLEEP = 0.4
    no_new_steps = 0
    total_steps = 0
    no_move_steps = 0
    while total_steps < MAX_SCROLL_STEPS:
        total_steps += 1
        moved = driver.execute_script("""
            function pickScrollable(startEl){
                let el = startEl;
                for (let i = 0; i < 12 && el; ++i) {
                    const st = getComputedStyle(el);
                    const canScroll = (st.overflowY === 'auto' || st.overflowY === 'scroll') && (el.scrollHeight > el.clientHeight + 10);
                    if (canScroll) return el;
                    el = el.parentElement;
                }
                return startEl;
            }
            const start = arguments[0];
            const target = pickScrollable(start);
            const before = target.scrollTop;
            target.scrollTop = before + 1200;
            return target.scrollTop !== before;
        """, element)
        if moved:
            no_move_steps = 0
        else:
            no_move_steps += 1
        if not moved:
            _ = driver.execute_script("""
                function pickScrollable(startEl){
                    let el = startEl;
                    for (let i = 0; i < 12 && el; ++i) {
                        const st = getComputedStyle(el);
                        const canScroll = (st.overflowY === 'auto' || st.overflowY === 'scroll') && (el.scrollHeight > el.clientHeight + 10);
                        if (canScroll) return el;
                        el = el.parentElement;
                    }
                    return startEl;
                }
                const start = arguments[0];
                const target = pickScrollable(start);
                target.dispatchEvent(new WheelEvent('wheel', {deltaY: 1200, bubbles: true, cancelable: true}));
                return true;
            """, element)
        if no_move_steps >= 50:
            if configure["predefined"]["scroll_to_bottom_tip"] in driver.page_source :
                break
            no_move_steps = 0
        time.sleep(STEP_SLEEP)
        cur_ids = collect_user_ids()
        before_size = len(seen_user_ids)
        seen_user_ids |= cur_ids
        after_size = len(seen_user_ids)
        grew = (after_size != before_size)
        if grew:
            no_new_steps = 0
        else:
            no_new_steps += 1
        if total_steps % 50 == 0 or grew:
            print(f"[scroll] step={total_steps} moved={moved} grew={grew} users={after_size} no_new={no_new_steps}")
        if no_new_steps >= NO_NEW_LIMIT:
            print(f"[scroll] reached bottom: no new users for {no_new_steps} steps. users={after_size}")
            break
    basic_path = os.path.dirname(os.path.abspath(__file__))
    if configure["path"]["basic"] != "" :
        basic_path = configure["path"]["basic"]
    with open(utility.path_add(basic_path, configure["path"]["following_users"]), "a+", encoding = "utf-8") as f :
        f.seek(0)
        existing_set = set([line.strip() for line in f.read().splitlines() if line.strip()])
        for user_id in seen_user_ids :
            url = f"https://www.douyin.com/user/{user_id}"
            if url in existing_set :
                continue
            f.write(url + "\n")
            existing_set.add(url)

if __name__ == "__main__" :
    configure = json.load(open("./config.json", 'r', encoding = "utf-8"))
    save_following(utility.get_chrome(configure), configure)