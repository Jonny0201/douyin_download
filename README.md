# 如何使用

本项目仅针对中国区抖音, 即 douyin, 不是 TikTok. 本项目未经过严格测试, 仅在我所需的场景下运行正常, 有问题带场景提 issue.

首先你需要了解整体结构, 项目总共提供了三个可用的工具 :

- `download.py` : 下载作品;
- `get_folowing.py` : 拉取自己的关注;
- `get_posts.py` : 拉取一个页面上所有作品 (可以是一个用户页面, 也可以是自己的喜欢页面).

上面三个都可以独立运行. 另外, `config.json` 提供了可配置的选项 :
```json
{
    "predefined" : {
        // 你不需要关注这里的配置
    },
    "path" : {
        "basic" : "",   // 下载和数据保存的目录, 下面的这些文件或者文件夹都会放在这里. 如果留空, 就用脚本所在的文件夹
        "download_records" : "download_records",    // 记录文件, 存放已经下载过的页面, 避免重复下载
        "download_path" : "download",   // 下载的作品存放的目录
        "cookies" : "selenium_data",    // 使用的是
        "tmp" : "tmp",    // 下载过程中会产生一些中间数据, 这些数据需要磁盘的临时存储, 下载完成之后会清掉
        "following_users" : "following_users",    // 记录文件, 存放关注的用户
        "url" : "url",    // 记录文件, 存放需要下载的页面地址
        "exceptional_url" : "exceptional_url"   // 记录文件, 存放下载出现异常的页面地址
    },
    "page" : {
        "favorite_collection" : true,   // 是否需要下载我的收藏
        "like" : true,    // 是否需要下载我的喜欢
        "record" : false,   // 是否需要下载观看历史
        "watch_later" : false   // 是否需要下载稍后再看
    },
    "pull_new_following" : true,    // 是否拉取关注列表, 看看有没有新增的
    "scroll" : {
        "stop_times" : 0,   // 在程序檢測到頁面下滑到最底部之後, 再嘗試下滑 x 次 (至少會再下滑 10 次, 總共下滑 10 + x 次)
        "manually_check" : false,   // 在一个页面滑动到最底下之后, 再手动检查一下是否真的到达页面最底部
        "stop_while_meeting_exists" : true    // 如果下滑的过程中发现了一个已经下载过或者记录过的作品, 那么就停止向下滑动 (一般在第二次之后可以开启, 大幅加速获取作品的速度, 前提是第二次增量更新之前, 页面里面的作品已经都下载过了)
    },
    "last_download_request_throws" : false,   // 如果上次下载的时候有异常情况退出了, 那么把这个选项置为 true, 防止上次异常退出的那个作品下载不完全
    "specific_pages" : [
        // 不在上面范围之内, 但是想要下载作品的页面, 例如 https://douyin.com/user/abcd
        // 注意最好右鍵在新頁面打開, 貼新頁面的地址
    ]
}
```

如果你只想下载某一个页面的作品（例如某个用户主页，或者你自己点过赞的页面），可以按以下方式操作：

1. 直接把目标页面的 URL 填写到 `config.json` 里的 `specific_pages` 数组中，或者写入 `path.url` 对应的文件中（每行一个 URL）。
2. 如果你不确定页面里一共有多少作品，也可以先运行 `python get_posts.py`，先把该页面中的所有作品链接拉取出来，确认无误后再用于下载。
3. 运行 `python download.py`，程序会只针对这些页面进行滚动和抓取，并把作品下载到 `path.download_path` 指定的目录中。

这样就可以只针对你关心的某一个（或几个）页面进行下载，而不需要拉取关注列表或其它页面。

## 环境准备

- Python 3.9+.
- 安装依赖: `pip install -r requirements.txt`.
- 安装 Chrome 浏览器, 并确保 ChromeDriver 与浏览器版本匹配, 或使用 Selenium Manager 自动下载.
- 首次使用需要登录抖音网页, 之後脚本会复用 Selenium 的登录状态与 cookies.

## 通用配置说明

- 所有工具都会读取 `config.json`.
- `path.basic` 为空时, 默认使用脚本所在目录.
- `path.download_records` 用于去重, 已下载页面不会重复下载.
- `page.*` 用于控制是否抓取对应页面.
- `specific_pages` 用于添加自定义页面, 例如其它用户喜欢和收藏等.

## download.py: 下载作品

用途: 根据 `path.url` 或 `specific_pages` 中的页面地址, 下载对应页面内的作品资源.

使用步骤:

1. 在 `config.json` 中配置 `path.basic` 与下载相关路径.
2. 将需要下载的页面地址写入 `path.url` 对应的文件, 或填写到 `specific_pages` 数组.
3. 运行: `python download.py`.
4. 程序会自动滚动页面并抓取作品, 下载结果保存到 `path.download_path`.
5. 已处理过的页面会记录到 `path.download_records`, 避免重复下载.

注意:

- 支持视频, 图片, Live Photo, 具体以页面实际返回为准.
- 下载过程中会使用 `path.tmp` 作为临时目录, 完成后会清理.

## get_following.py: 拉取关注列表

用途: 拉取当前账号的关注用户列表, 并保存到 `path.following_users`.

使用步骤:

1. 确保已在浏览器中登录抖音.
2. 运行: `python get_folowing.py`.
3. 程序会自动滚动关注列表页面, 直到不再增长或需要人工确认.
4. 最终结果会按行写入 `path.following_users` 文件.

注意:

- 如果页面加载较慢, 可能需要多滚动几次.
- 当连续多次没有新增数据时, 程序会提示是否继续.

## get_posts.py: 拉取页面内所有作品链接

用途: 对任意一个作品列表页面进行滚动, 抓取其中所有作品链接, 并返回或保存为列表, 供后续下载使用.

使用步骤:

1. 打开需要抓取的页面, 例如用户主页, 喜欢页, 收藏页等.
2. 运行: `python get_posts.py`.
3. 程序会在指定的滚动容器内持续下滑, 直到不再新增作品或需要人工确认.
4. 最终会得到一个去重后的作品链接列表, 格式类似:
   - `https://www.douyin.com/video/xxxxxxxx`
   - `https://www.douyin.com/note/xxxxxxxx`

注意:

- 程序会自动规范化链接, 避免重复前缀或相对路径问题.
- 该工具通常用于辅助生成待下载的 URL 列表.

## 常见问题

- 注意抖音有验证机制, 不要一次性下载太多, 脚本拉取的并不是通过抖音提供的 API, 而是页面向下滑动;
- 出现验证码之后, 建议停止下载, 过一天再下载, 除非你特别急, 例如作者要删作品 (这种情况你甚至可以调用 `get_posts.py` 之后, 去搜索引擎搜索抖音下载工具手动下载);
- 下载完成之后, 如果目录下出现了 `exceptional_url` 这个文件, 就说明下载的过程中部分页面是失败的, 除非抖音变更了页面实现, 否则你可以再次运行. 运行几次之后仍然失败, 可以手动下载, 有空的话可以在 issue 上把链接贴上来;
- 目前发现极少部分长视频可能跑偏的问题, 例如视频 A 下载成视频 B, 这个看起来不是脚本的原因;