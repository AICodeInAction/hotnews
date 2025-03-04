import os
import logging
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

# 日志配置
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 输出格式
OUTPUT_FORMAT = "json"  # json, csv, excel

# 平台配置
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
        "use_api": True,
        "api_url": "https://36kr.com/api/newsflash/catalog",
        "web_url": "https://36kr.com/hot-list/catalog",
        "max_items": 30
    },
    "baidu": {
        "enabled": True,
        "use_api": True,
        "api_url": "https://top.baidu.com/api/board?platform=wise&tab=realtime",
        "web_url": "https://top.baidu.com/board?tab=realtime",
        "max_items": 30
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
        "use_api": True,
        "api_url": "https://weibo.com/ajax/side/hotSearch",
        "web_url": "https://s.weibo.com/top/summary",
        "max_items": 50
    },
    "douyin": {
        "enabled": True,
        "use_api": True,
        "api_url": "https://www.douyin.com/aweme/v1/web/hot/search/list/",
        "web_url": "https://www.douyin.com/hot",
        "max_items": 50
    },
    "hupu": {
        "enabled": True,
        "use_api": False,
        "api_url": "",
        "web_url": "https://bbs.hupu.com/all-gambia",
        "max_items": 30
    },
    "douban": {
        "enabled": True,
        "use_api": False,
        "api_url": "",
        "web_url": "https://www.douban.com/group/explore",
        "max_items": 30
    },
    "it_news": {
        "enabled": True,
        "use_api": True,
        "api_url": "https://rsshub.app/36kr/news/latest",
        "web_url": "https://36kr.com/information/technology",
        "max_items": 30
    }
}

# 设置爬虫配置
class CrawlerConfig:
    # 添加DATA_DIR作为类属性
    DATA_DIR = DATA_DIR
    
    # 添加PLATFORMS作为类属性
    PLATFORMS = PLATFORMS
    
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
    LOG_LEVEL = LOG_LEVEL
    
    def __init__(self, platform):
        self.platform = platform
        self.config = self.PLATFORMS.get(platform, {})
        self.enabled = self.config.get("enabled", False)
        self.use_api = self.config.get("use_api", False)
        self.api_url = self.config.get("api_url", "")
        self.web_url = self.config.get("web_url", "")
        self.max_items = self.config.get("max_items", 30)
        
        # 创建数据目录
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # 创建日志目录
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        
        # 设置日志
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger(f"{self.platform}_crawler")
        logger.setLevel(LOG_LEVEL)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL)
        console_formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # 文件处理器
        log_file = os.path.join(LOG_DIR, f"{self.platform}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(LOG_LEVEL)
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def get_output_file(self):
        """获取输出文件路径"""
        date_str = datetime.now().strftime("%Y%m%d")
        if OUTPUT_FORMAT == "json":
            return os.path.join(DATA_DIR, f"{self.platform}_{date_str}.json")
        elif OUTPUT_FORMAT == "csv":
            return os.path.join(DATA_DIR, f"{self.platform}_{date_str}.csv")
        elif OUTPUT_FORMAT == "excel":
            return os.path.join(DATA_DIR, f"{self.platform}_{date_str}.xlsx")
        else:
            return os.path.join(DATA_DIR, f"{self.platform}_{date_str}.json")
    
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