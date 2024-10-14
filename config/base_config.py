# 基础配置
PLATFORM = "xhs"
KEYWORDS = "编程副业,编程兼职"
LOGIN_TYPE = "cookie"  # qrcode or phone or cookie
COOKIES = "unread={%22ub%22:%2266b43df3000000000d030f12%22%2C%22ue%22:%2266c5d40d000000001d0169d0%22%2C%22uc%22:15}; acw_tc=66db0c2924dfb1a510bf95dc5c8bcec3d968d28b1d7917b7d5735d265bf66c26; sec_poison_id=2afce1b6-b1ad-418b-91b5-41deaa010fa4; websectiga=9730ffafd96f2d09dc024760e253af6ab1feb0002827740b95a255ddf6847fc8; gid=yjy4WYWWYqKiyjy4WYW2fCD9ydVlYj2fF77IY21VKEA3quq886UqkF8884y2jq88YdKSJdKS; webBuild=4.31.2; xsecappid=xhs-pc-web; web_session=040069b38b466d07ae330df2f3344b02e84074; a1=191733d2e9eq48hsk17euo9lcbq6x1ll81iheeqfk30000219643; webId=41fdb0d06b343756d1bd5a56ff8cc11c; abRequestId=ca11363f-a630-5b8d-8108-b6907da90113"
#COOKIES = "gid=yjy4WYWWYqKiyjy4WYW2fCD9ydVlYj2fF77IY21VKEA3quq886UqkF8884y2jq88YdKSJdKS; unread={%22ub%22:%2266c31818000000001d015b45%22%2C%22ue%22:%2266c5d40d000000001d0169d0%22%2C%22uc%22:31}; webBuild=4.31.2; xsecappid=xhs-pc-web; sec_poison_id=05203f83-cffb-41d1-a977-4326c05416f1; websectiga=2845367ec3848418062e761c09db7caf0e8b79d132ccdd1a4f8e64a11d0cac0d; web_session=040069b38b466d07ae330df2f3344b02e84074; acw_tc=21fa96335627c37833a1bc803abe5dfca7e9a134a37a365770a32bfd2b561266; a1=191733d2e9eq48hsk17euo9lcbq6x1ll81iheeqfk30000219643; webId=41fdb0d06b343756d1bd5a56ff8cc11c; abRequestId=ca11363f-a630-5b8d-8108-b6907da90113"
# 具体值参见media_platform.xxx.field下的枚举值，暂时只支持小红书
SORT_TYPE = "popularity_descending"
# 具体值参见media_platform.xxx.field下的枚举值，暂时只支持抖音
PUBLISH_TIME_TYPE = 0
CRAWLER_TYPE = "search"  # 爬取类型，search(关键词搜索) | detail(帖子详情)| creator(创作者主页数据)

# 是否开启 IP 代理
ENABLE_IP_PROXY = True

# 代理IP池数量
IP_PROXY_POOL_COUNT = 1

# 代理IP提供商名称
IP_PROXY_PROVIDER_NAME = "static"

# 静态代理
#123proxy IP_PROXY_LIST = ["45.86.230.119:36932:unewyear62396:HdYtLULoztav"]
IP_PROXY_LIST = ["proxy.proxy302.com:2222:IEZlKqlG:g7tUeBVkyva4gGSv"]
#通过使用隧道代理，无需软件频繁提取IP，代理隧道在云端自动切换请求的代理IP
        
# 设置为True不会打开浏览器（无头浏览器）
# 设置False会打开一个浏览器
# 小红书如果一直扫码登录不通过，打开浏览器手动过一下滑动验证码
# 抖音如果一直提示失败，打开浏览器看下是否扫码登录之后出现了手机号验证，如果出现了手动过一下再试。
HEADLESS = True

# 是否保存登录状态
SAVE_LOGIN_STATE = True

# 数据保存类型选项配置,支持三种类型：csv、db、json, 最好保存到DB，有排重的功能。
SAVE_DATA_OPTION = "db"  # csv or db or json

# 用户浏览器缓存的浏览器文件配置
USER_DATA_DIR = "%s_user_data_dir"  # %s will be replaced by platform name

# 爬取开始页数 默认从第一页开始
START_PAGE = 1

# 爬取视频/帖子的数量控制
CRAWLER_MAX_NOTES_COUNT = 100

# 并发爬虫数量控制
MAX_CONCURRENCY_NUM = 1

# 是否开启爬图片模式, 默认不开启爬图片
ENABLE_GET_IMAGES = False

# 是否开启爬评论模式, 默认不开启爬评论
ENABLE_GET_COMMENTS = False

# 是否开启爬二级评论模式, 默认不开启爬二级评论
# 老版本项目使用了 db, 则需参考 schema/tables.sql line 287 增加表字段
ENABLE_GET_SUB_COMMENTS = False

# 抓小红书creator页面时，是否抓帖子详情。False则只抓帖子列表
ENABLE_GET_NOTES = False

# 指定小红书需要爬虫的笔记ID列表
XHS_SPECIFIED_ID_LIST = [
    "6422c2750000000027000d88",
    # ........................
]

# 指定抖音需要爬取的ID列表
DY_SPECIFIED_ID_LIST = [
    "7280854932641664319",
    "7202432992642387233"
    # ........................
]

# 指定快手平台需要爬取的ID列表
KS_SPECIFIED_ID_LIST = [
    "3xf8enb8dbj6uig",
    "3x6zz972bchmvqe"
]

# 指定B站平台需要爬取的视频bvid列表
BILI_SPECIFIED_ID_LIST = [
    "BV1d54y1g7db",
    "BV1Sz4y1U77N",
    "BV14Q4y1n7jz",
    # ........................
]

# 指定微博平台需要爬取的帖子列表
WEIBO_SPECIFIED_ID_LIST = [
    "4982041758140155",
    # ........................
]

# 指定weibo创作者ID列表
WEIBO_CREATOR_ID_LIST = [
    "5533390220",
    # ........................
]

# 指定贴吧需要爬取的帖子列表
TIEBA_SPECIFIED_ID_LIST = [

]

# 指定贴吧名称列表，爬取该贴吧下的帖子
TIEBA_NAME_LIST = [
    # "盗墓笔记"
]

TIEBA_CREATOR_URL_LIST = [
    "https://tieba.baidu.com/home/main/?id=tb.1.7f139e2e.6CyEwxu3VJruH_-QqpCi6g&fr=frs",
    # ........................
]

# 指定小红书创作者ID列表
XHS_CREATOR_ID_LIST = [
    "64084629000000001001eba2",
    # ........................
]

# 指定小红书创作者ID列表文件
XHS_CREATOR_ID_LIST_FILE = './xhs_creators.txt'
ENABLE_XHS_CREATOR_ID_CHECKPOINT = True
# 每次运行最多抓取的作者数，-1则不限制
XHS_CREATOR_MAX_COUNT = 250

# 指定Dy创作者ID列表(sec_id)
DY_CREATOR_ID_LIST = [
    "MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE",
    # ........................
]

# 指定bili创作者ID列表(sec_id)
BILI_CREATOR_ID_LIST = [
    "20813884",
    # ........................
]

# 指定快手创作者ID列表
KS_CREATOR_ID_LIST = [
    "3x4sm73aye7jq7i",
    # ........................
]

# 翻页数。目前仅xhs creator支持
PAGE_COUNT = 2

# 词云相关
# 是否开启生成评论词云图
ENABLE_GET_WORDCLOUD = False
# 自定义词语及其分组
# 添加规则：xx:yy 其中xx为自定义添加的词组，yy为将xx该词组分到的组名。
CUSTOM_WORDS = {
    '零几': '年份',  # 将“零几”识别为一个整体
    '高频词': '专业术语'  # 示例自定义词
}

# 停用(禁用)词文件路径
STOP_WORDS_FILE = "./docs/hit_stopwords.txt"

# 中文字体文件路径
FONT_PATH = "./docs/STZHONGS.TTF"

# 是否保存api返回的原始结果
SAVE_RAW = True
