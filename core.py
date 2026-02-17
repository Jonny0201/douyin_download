from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import ffmpeg
import shutil
import time
import utility

def download(driver, configure, url_list) :
    count = 0
    exceptional_url = set()
    basic_path = os.path.dirname(os.path.abspath(__file__))
    if configure["path"]["basic"] != "" :
        basic_path = configure["path"]["basic"]
    download_records = open(utility.path_add(basic_path, configure["path"]["download_records"]), "a+", encoding = "utf-8")
    download_records.seek(0)
    downloaded = set(download_records.read().splitlines())
    download_path = utility.path_add(basic_path, configure["path"]["download_path"])
    tmp_path = utility.path_add(basic_path, configure["path"]["tmp"])
    for url in url_list :
        count += 1
        print("left : " + str(len(url_list) - count))
        if url in downloaded :
            continue
        id = url.split('/')[-1]
        try :
            if "/video/" in url :
                file_name = id + ".mp4"
                if os.path.exists(utility.path_add(download_path, file_name)) :
                    raise Exception("save to downloaded list")
                driver.get(url)
                if len(driver.find_elements(By.CLASS_NAME, configure["predefined"]["error_page_tag"])) > 0 :
                    raise Exception("save to downloaded list")
                try :
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "xgplayer-play")))
                except :
                    raise Exception("save to exceptional list")
                if len(driver.find_elements(By.ID, "captcha_container")) > 0 :
                    input("页面出现了验证码, 请先处理验证码, 处理完成之后在终端机中按下回车")
                try :
                    driver.find_element(By.CLASS_NAME, "xgplayer-play").click()
                except :
                    raise Exception("save to exceptional list")
                video_urls = None
                try :
                    video_urls = driver.find_elements(By.TAG_NAME, "source")
                except :
                    raise Exception("save to exceptional list")
                video = None
                for video_url in video_urls :
                    try :
                        video = utility.request(video_url.get_attribute("src"))
                        video.raise_for_status()
                    except :
                        continue
                    break
                if video is None :
                    logs = driver.get_log("performance")
                    video_url = None
                    audio_url = None
                    for entry in logs :
                        msg = json.loads(entry["message"])["message"]
                        if msg.get("method") != "Network.responseReceived" :
                            continue
                        params = msg.get("params", {})
                        response = params.get("response", {})
                        response_url = response.get("url", "")
                        if "media-video-hvc1" in response_url :
                            video_url = response_url
                        if "media-audio-und-mp4a" in response_url :
                            audio_url = response_url
                        if video_url is not None and audio_url is not None :
                            break
                    if video_url is None :
                        raise Exception("save to exceptional list")
                    try :
                        video = utility.request(video_url)
                        video.raise_for_status()
                    except :
                        raise Exception("save to exceptional list")
                    with open(utility.path_add(tmp_path, "video.mp4"), "wb") as f :
                        f.write(video.content)
                        f.close()
                    if audio_url is not None :
                        try :
                            audio = utility.request(audio_url)
                            audio.raise_for_status()
                        except :
                            raise Exception("save to exceptional list")
                        with open(utility.path_add(tmp_path, "audio.m4a"), "wb") as f :
                            f.write(audio.content)
                            f.close()
                    if os.path.exists(utility.path_add(tmp_path, "video.mp4")) and os.path.exists(utility.path_add(tmp_path, "audio.m4a")) :
                        (ffmpeg.input(utility.path_add(tmp_path, "video.mp4")).output(
                                ffmpeg.input(utility.path_add(tmp_path, "audio.m4a")), utility.path_add(download_path, file_name),
                                vcodec = "copy", acodec = "copy", movflags = "+faststart").overwrite_output().run())
                        os.remove(utility.path_add(tmp_path, "video.mp4"))
                        os.remove(utility.path_add(tmp_path, "audio.m4a"))
                    else :
                        shutil.move(utility.path_add(tmp_path, "video.mp4"), utility.path_add(download_path, file_name))
                else :
                    with open(utility.path_add(download_path, file_name), "wb") as file:
                        file.write(video.content)
                        file.close()
            elif "/note/" in url :
                if not configure["last_download_request_throws"] :
                    if (url in downloaded or os.path.exists(utility.path_add(download_path, f"{id}.webp")) or
                            os.path.exists(utility.path_add(download_path, f"{id}_1.webp"))) :
                        raise Exception("save to downloaded list")
                driver.get(url)
                if len(driver.find_elements(By.CLASS_NAME, configure["predefined"]["error_page_tag"])) > 0 :
                    raise Exception("save to downloaded list")
                try :
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "xgplayer-play")))
                except :
                    raise Exception("save to exceptional list")
                if len(driver.find_elements(By.ID, "captcha_container")) > 0 :
                    input("页面出现了验证码, 请先处理验证码, 处理完成之后在终端机中按下回车")
                try :
                    driver.find_element(By.CLASS_NAME, "xgplayer-play").click()
                except :
                    pass
                media_number = None
                skip = False
                try :
                    media_number = driver.find_element(By.CLASS_NAME, configure["predefined"]["number_of_media_tag"])
                except :        # only an image or live photo
                    file_name = id + ".webp"
                    if os.path.exists(utility.path_add(download_path, file_name)) :
                        raise Exception("save to downloaded list")
                    try :
                        image = driver.find_element(By.CLASS_NAME, configure["predefined"]["image_tag"])
                    except :
                        raise Exception("save to exceptional list")
                    image = image.find_element(By.TAG_NAME, "img").get_attribute("src")
                    try :
                        image = utility.request(image)
                        image.raise_for_status()
                    except :
                        pass
                    if image is None :
                        raise Exception("save to exceptional list")
                    with open(utility.path_add(download_path, file_name), "wb") as file:
                        file.write(image.content)
                        file.close()
                    live_photo = None
                    try :
                        live_photo = driver.find_element(By.CLASS_NAME, configure["predefined"]["live_photo_tag"])
                    except :
                        pass
                    if live_photo is not None :
                        live_photo_video_urls = live_photo.find_elements(By.TAG_NAME, "source")
                        live_photo_video = None
                        for live_photo_video_url in live_photo_video_urls :
                            try :
                                live_photo_video = utility.request(live_photo_video_url.get_attribute("src"))
                                live_photo_video.raise_for_status()
                            except :
                                continue
                            break
                        if live_photo_video is None :
                            exceptional_url.add(url)
                        else :
                            with open(utility.path_add(download_path, id + "_live.mp4"), "wb") as file:
                                file.write(live_photo_video.content)
                                file.close()
                    skip = True
                if not skip :
                    media_number = int(media_number.find_element(By.XPATH, "./* [last()]").text.strip())
                    progresses = driver.find_elements(By.CLASS_NAME, "xgplayer-progress-inner")
                    images = driver.find_elements(By.CLASS_NAME, "dySwiperSlide")
                    if len(progresses) != media_number or len(images) != media_number :
                        raise Exception("save to exceptional list")
                    for i in range(media_number) :
                        progresses[i].click()
                        if not os.path.exists(utility.path_add(download_path, id + "_" + str(i + 1) + ".webp")) :
                            image = (images[i].find_element(By.CLASS_NAME, configure["predefined"]["image_tag"]).
                                     find_element(By.TAG_NAME, "img").get_attribute("src"))
                            try :
                                image = utility.request(image)
                                image.raise_for_status()
                            except :
                                raise Exception("save to exceptional list")
                            with open(utility.path_add(download_path, id + f"_{str(i + 1)}.webp"), "wb") as file:
                                file.write(image.content)
                                file.close()
                        if not os.path.exists(utility.path_add(download_path, id + f"_live_{str(i + 1)}.mp4")) :
                            live_photo = None
                            try :
                                live_photo = images[i].find_element(By.CLASS_NAME, configure["predefined"]["live_photo_tag"])
                            except :
                                pass
                            if live_photo is not None :
                                live_photo_video_urls = live_photo.find_elements(By.TAG_NAME, "source")
                                live_photo_video = None
                                for live_photo_video_url in live_photo_video_urls :
                                    try :
                                        live_photo_video = utility.request(live_photo_video_url.get_attribute("src"))
                                        live_photo_video.raise_for_status()
                                    except :
                                        continue
                                    break
                                if live_photo_video is None :
                                    exceptional_url.add(url)
                                    continue
                                with open(utility.path_add(download_path, id + f"_live_{str(i + 1)}.mp4"), "wb") as file:
                                    file.write(live_photo_video.content)
                                    file.close()
            else :
                raise Exception("save to exceptional list")
            downloaded.add(url)
            download_records.write(url + '\n')
            download_records.flush()
        except Exception as e :
            case = str(e)
            if case == "save to downloaded list" :
                downloaded.add(url)
                download_records.write(url + '\n')
                download_records.flush()
            elif case == "save to exceptional list" :
                if (len(driver.find_elements(By.CLASS_NAME, configure["predefined"]["error_page_tag"])) > 0 or
                        driver.current_url.startswith("https://www.douyin.com/video/") or
                        driver.current_url.startswith("https://www.douyin.com/note/")) :
                    downloaded.add(url)
                    download_records.write(url + '\n')
                    download_records.flush()
                else :
                    exceptional_url.add(url)
            else :
                exceptional_url.add(url)
    print("this download request done!")
    return list(exceptional_url)
def download2(driver, configure, url_list) :
    def _abs_douyin_url(href) :
        if href is None :
            return None
        href = href.strip()
        if href.startswith("//") :
            return "https:" + href
        if href.startswith("/") :
            return "https://www.douyin.com" + href
        if href.startswith("http://") or href.startswith("https://") :
            return href
        return urljoin("https://www.douyin.com/", href)
    def _iter_stream_write(response, file_path, chunk_size = 1024 * 256, stall_timeout = 30) :
        last_progress = time.time()
        bytes_written = 0
        with open(file_path, "wb") as f :
            for chunk in response.iter_content(chunk_size = chunk_size) :
                now = time.time()
                if chunk :
                    f.write(chunk)
                    bytes_written += len(chunk)
                    last_progress = now
                else :
                    if now - last_progress >= stall_timeout :
                        raise Exception("save to exceptional list")
        return bytes_written
    def _request_stream(url, max_tries = 3, connect_timeout = 10, stall_timeout = 30) :
        last_exc = None
        for _ in range(max_tries) :
            try :
                resp = utility.request(url, timeout = (connect_timeout, stall_timeout + 5))
                resp.raise_for_status()
                return resp
            except Exception as e :
                last_exc = e
                try :
                    if "resp" in locals() and resp is not None :
                        resp.close()
                except :
                    pass
                time.sleep(1)
        raise last_exc
    def _resolve_video_media(driver, configure, post_url, tmp_path) :
        driver.get(post_url)
        if len(driver.find_elements(By.CLASS_NAME, configure["predefined"]["error_page_tag"])) > 0 :
            raise Exception("save to downloaded list")
        try :
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "xgplayer-play")))
        except :
            raise Exception("save to exceptional list")
        if len(driver.find_elements(By.ID, "captcha_container")) > 0 :
            input("页面出现了验证码, 请先处理验证码, 处理完成之后在终端机中按下回车")
        try :
            driver.find_element(By.CLASS_NAME, "xgplayer-play").click()
        except :
            pass
        video_urls = []
        try :
            sources = driver.find_elements(By.TAG_NAME, "source")
            for s in sources :
                src = s.get_attribute("src")
                src = _abs_douyin_url(src)
                if src is not None :
                    video_urls.append(src)
        except :
            pass
        for src in video_urls :
            try :
                resp = utility.request(src)
                resp.raise_for_status()
                return {"mode" : "single", "video_url" : src}
            except :
                continue
        logs = driver.get_log("performance")
        video_url = None
        audio_url = None
        for entry in logs :
            try :
                msg = json.loads(entry["message"])["message"]
            except :
                continue
            if msg.get("method") != "Network.responseReceived" :
                continue
            params = msg.get("params", {})
            response = params.get("response", {})
            resp_url = response.get("url", "")
            if "media-video-hvc1" in resp_url :
                video_url = resp_url
            if "media-audio-und-mp4a" in resp_url :
                audio_url = resp_url
            if video_url is not None and audio_url is not None :
                break
        if video_url is None :
            raise Exception("save to exceptional list")
        return {"mode" : "av", "video_url" : video_url, "audio_url" : audio_url}
    def _resolve_note_media(driver, configure, post_url) :
        driver.get(post_url)
        if len(driver.find_elements(By.CLASS_NAME, configure["predefined"]["error_page_tag"])) > 0 :
            raise Exception("save to downloaded list")
        try :
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except :
            raise Exception("save to exceptional list")
        if len(driver.find_elements(By.ID, "captcha_container")) > 0 :
            input("页面出现了验证码, 请先处理验证码, 处理完成之后在终端机中按下回车")
        has_player = len(driver.find_elements(By.CLASS_NAME, "xgplayer-play")) > 0
        if has_player :
            try :
                plan = _resolve_video_media(driver, configure, post_url, None)
                return {"kind" : "video", "plan" : plan}
            except :
                pass
        media_number_el = None
        try :
            media_number_el = driver.find_element(By.CLASS_NAME, configure["predefined"]["number_of_media_tag"])
        except :
            media_number_el = None
        if media_number_el is None :
            image_el = None
            try :
                image_el = driver.find_element(By.CLASS_NAME, configure["predefined"]["image_tag"]).find_element(By.TAG_NAME, "img")
            except :
                raise Exception("save to exceptional list")
            image_url = _abs_douyin_url(image_el.get_attribute("src"))
            live_video_url = None
            try :
                live_photo = driver.find_element(By.CLASS_NAME, configure["predefined"]["live_photo_tag"])
                live_sources = live_photo.find_elements(By.TAG_NAME, "source")
                for s in live_sources :
                    src = _abs_douyin_url(s.get_attribute("src"))
                    if src is None :
                        continue
                    try :
                        r = utility.request(src)
                        r.raise_for_status()
                        live_video_url = src
                        break
                    except :
                        continue
            except :
                pass
            return {"kind" : "single", "image_url" : image_url, "live_video_url" : live_video_url}
        media_number = int(media_number_el.find_element(By.XPATH, "./* [last()]").text.strip())
        progresses = driver.find_elements(By.CLASS_NAME, "xgplayer-progress-inner")
        images = driver.find_elements(By.CLASS_NAME, "dySwiperSlide")
        if len(images) < media_number :
            raise Exception("save to exceptional list")
        items = []
        for i in range(media_number) :
            try :
                if i < len(progresses) :
                    progresses[i].click()
            except :
                pass
            image_url = None
            try :
                image_url = images[i].find_element(By.CLASS_NAME, configure["predefined"]["image_tag"]).find_element(By.TAG_NAME, "img").get_attribute("src")
            except :
                raise Exception("save to exceptional list")
            image_url = _abs_douyin_url(image_url)
            live_video_url = None
            try :
                live_photo = images[i].find_element(By.CLASS_NAME, configure["predefined"]["live_photo_tag"])
                live_sources = live_photo.find_elements(By.TAG_NAME, "source")
                for s in live_sources :
                    src = _abs_douyin_url(s.get_attribute("src"))
                    if src is None :
                        continue
                    try :
                        r = utility.request(src)
                        r.raise_for_status()
                        live_video_url = src
                        break
                    except :
                        continue
            except :
                pass
            items.append({"image_url" : image_url, "live_video_url" : live_video_url})
        return {"kind" : "multi", "items" : items}
    exceptional_url = set()
    basic_path = os.path.dirname(os.path.abspath(__file__))
    if configure["path"]["basic"] != "" :
        basic_path = configure["path"]["basic"]
    download_path = utility.path_add(basic_path, configure["path"]["download_path"])
    tmp_path = utility.path_add(basic_path, configure["path"]["tmp"])
    download_records_path = utility.path_add(basic_path, configure["path"]["download_records"])
    with open(download_records_path, "a+", encoding = "utf-8") as download_records :
        download_records.seek(0)
        downloaded = set(download_records.read().splitlines())
        for post_url in url_list :
            if post_url in downloaded :
                continue
            post_id = post_url.split("/")[-1]
            try :
                plan = []
                if "/video/" in post_url :
                    file_name = post_id + ".mp4"
                    final_path = utility.path_add(download_path, file_name)
                    if os.path.exists(final_path) :
                        raise Exception("save to downloaded list")
                    vplan = _resolve_video_media(driver, configure, post_url, tmp_path)
                    if vplan["mode"] == "single" :
                        plan.append({"type" : "stream", "remote" : vplan["video_url"], "local" : final_path})
                    else :
                        plan.append({"type" : "merge", "video" : vplan["video_url"], "audio" : vplan.get("audio_url"), "final" : final_path, "id" : post_id})
                elif "/note/" in post_url :
                    n = _resolve_note_media(driver, configure, post_url)
                    if n["kind"] == "video" :
                        vplan = n["plan"]
                        file_name = post_id + ".mp4"
                        final_path = utility.path_add(download_path, file_name)
                        if os.path.exists(final_path) :
                            raise Exception("save to downloaded list")
                        if vplan["mode"] == "single" :
                            plan.append({"type" : "stream", "remote" : vplan["video_url"], "local" : final_path})
                        else :
                            plan.append({"type" : "merge", "video" : vplan["video_url"], "audio" : vplan.get("audio_url"), "final" : final_path, "id" : post_id})
                    elif n["kind"] == "single" :
                        img_path = utility.path_add(download_path, post_id + ".webp")
                        if os.path.exists(img_path) :
                            raise Exception("save to downloaded list")
                        plan.append({"type" : "stream", "remote" : n["image_url"], "local" : img_path})
                        if n.get("live_video_url") is not None :
                            live_path = utility.path_add(download_path, post_id + "_live.mp4")
                            if not os.path.exists(live_path) :
                                plan.append({"type" : "stream", "remote" : n["live_video_url"], "local" : live_path})
                    else :
                        items = n["items"]
                        for i, it in enumerate(items) :
                            idx = i + 1
                            img_path = utility.path_add(download_path, post_id + "_" + str(idx) + ".webp")
                            if not os.path.exists(img_path) :
                                plan.append({"type" : "stream", "remote" : it["image_url"], "local" : img_path})
                            if it.get("live_video_url") is not None :
                                live_path = utility.path_add(download_path, post_id + "_live_" + str(idx) + ".mp4")
                                if not os.path.exists(live_path) :
                                    plan.append({"type" : "stream", "remote" : it["live_video_url"], "local" : live_path})
                else :
                    raise Exception("save to exceptional list")
                for task in plan :
                    if task["type"] == "stream" :
                        remote = task["remote"]
                        local = task["local"]
                        if remote is None :
                            raise Exception("save to exceptional list")
                        try :
                            resp = _request_stream(remote, max_tries = 3, connect_timeout = 10, stall_timeout = 30)
                            _iter_stream_write(resp, local, chunk_size = 1024 * 256, stall_timeout = 30)
                        finally :
                            try :
                                resp.close()
                            except :
                                pass
                    else :
                        v_url = task["video"]
                        a_url = task.get("audio")
                        pid = task["id"]
                        vtmp = utility.path_add(tmp_path, "video_" + pid + ".mp4")
                        atmp = utility.path_add(tmp_path, "audio_" + pid + ".m4a")
                        resp = None
                        try :
                            resp = _request_stream(v_url, max_tries = 3, connect_timeout = 10, stall_timeout = 30)
                            _iter_stream_write(resp, vtmp, chunk_size = 1024 * 256, stall_timeout = 30)
                        finally :
                            try :
                                if resp is not None :
                                    resp.close()
                            except :
                                pass
                        if a_url is not None :
                            resp = None
                            try :
                                resp = _request_stream(a_url, max_tries = 3, connect_timeout = 10, stall_timeout = 30)
                                _iter_stream_write(resp, atmp, chunk_size = 1024 * 256, stall_timeout = 30)
                            finally :
                                try :
                                    if resp is not None :
                                        resp.close()
                                except :
                                    pass
                        if os.path.exists(vtmp) and a_url is not None and os.path.exists(atmp) :
                            (ffmpeg.input(vtmp).output(ffmpeg.input(atmp), task["final"], vcodec = "copy", acodec = "copy", movflags = "+faststart").overwrite_output().run())
                            os.remove(vtmp)
                            os.remove(atmp)
                        else :
                            shutil.move(vtmp, task["final"])
                downloaded.add(post_url)
                download_records.write(post_url + "\n")
                download_records.flush()
            except Exception as e :
                case = str(e)
                if case == "save to downloaded list" :
                    downloaded.add(post_url)
                    download_records.write(post_url + "\n")
                    download_records.flush()
                elif case == "save to exceptional list" :
                    exceptional_url.add(post_url)
                else :
                    exceptional_url.add(post_url)
    return list(exceptional_url)