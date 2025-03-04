import os
from datetime import datetime
from dotenv import load_dotenv
import json

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据保存目录
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 设置爬虫配置
class CrawlerConfig:
    # 通用配置
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    REQUEST_TIMEOUT = 10  # 秒
    RETRY_TIMES = 3
    RETRY_DELAY = 2  # 秒
    
    # 代理设置
    USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
    PROXY_LIST_PATH = os.getenv("PROXY_LIST", os.path.join(ROOT_DIR, "proxies.txt"))
    
    # 输出配置
    OUTPUT_FORMATS = os.getenv("OUTPUT_FORMAT", "json").split(",")
    SAVE_TO_DB = os.getenv("SAVE_TO_DB", "false").lower() == "true"
    
    # 调度配置
    SCHEDULE_INTERVAL = int(os.getenv("SCHEDULE_INTERVAL", "60"))  # 分钟
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # 平台特定配置
    PLATFORMS = {
        "zhihu": {
            "enabled": True,
            "use_api": True,
            "api_url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50",
            "web_url": "https://www.zhihu.com/hot",
            "max_items": 50
        },
        "36kr": {
            "enabled": True,
            "use_api": False,
            "web_url": "https://36kr.com/hot-list/catalog",
            "max_items": 50
        },
        "baidu": {
            "enabled": True,
            "use_api": False,
            "web_url": "https://top.baidu.com/board?tab=realtime",
            "max_items": 50
        },
        "bilibili": {
            "enabled": True,
            "use_api": True,
            "api_url": "https://api.bilibili.com/x/web-interface/popular/series/one",
            "web_url": "https://www.bilibili.com/v/popular/rank/all",
            "max_items": 100
        },
        "weibo": {
            "enabled": True,
            "use_api": False,
            "web_url": "https://s.weibo.com/top/summary",
            "max_items": 50
        },
        "douyin": {
            "enabled": True,
            "use_api": False,
            "web_url": "https://www.douyin.com/hot",
            "max_items": 50,
            "use_selenium": True
        },
        "hupu": {
            "enabled": True,
            "use_api": False,
            "web_url": "https://bbs.hupu.com/all-gambia",
            "max_items": 50
        },
        "douban": {
            "enabled": True,
            "use_api": False,
            "web_url": "https://www.douban.com/group/explore",
            "max_items": 50
        },
        "it_news": {
            "enabled": True,
            "use_api": False,
            "web_url": "https://36kr.com/information/technology",
            "max_items": 50
        }
    }

    @staticmethod
    def get_output_filename(platform, fmt="json"):
        """生成输出文件名"""
        date_str = datetime.now().strftime("%Y%m%d")
        return os.path.join(DATA_DIR, f"{platform}_{date_str}.{fmt}")
    
    @staticmethod
    def save_data(platform, data, fmt="json"):
        """保存数据到文件"""
        filename = CrawlerConfig.get_output_filename(platform, fmt)
        
        if fmt == "json":
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif fmt == "csv":
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding="utf-8")
        
        return filename 