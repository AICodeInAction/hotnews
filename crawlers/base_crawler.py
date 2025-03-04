import logging
from abc import ABC, abstractmethod
from utils.helpers import make_request, get_soup, normalize_data
from config.config import CrawlerConfig

class BaseCrawler(ABC):
    """基础爬虫类，所有平台爬虫将继承这个类"""
    
    def __init__(self, platform_name):
        self.logger = logging.getLogger(f"HotNews.{platform_name}")
        self.platform_name = platform_name
        
        # 获取平台配置
        if platform_name not in CrawlerConfig.PLATFORMS:
            raise ValueError(f"未知平台: {platform_name}")
            
        self.config = CrawlerConfig.PLATFORMS[platform_name]
        self.enabled = self.config.get("enabled", True)
        self.use_api = self.config.get("use_api", False)
        self.api_url = self.config.get("api_url")
        self.web_url = self.config.get("web_url")
        self.max_items = self.config.get("max_items", 50)
        
    def crawl(self):
        """爬取热点数据"""
        if not self.enabled:
            self.logger.info(f"{self.platform_name} 平台未启用")
            return []
            
        try:
            self.logger.info(f"开始爬取 {self.platform_name} 的热点数据")
            
            # 根据配置选择API或网页爬取
            if self.use_api and self.api_url:
                items = self.crawl_by_api()
            else:
                items = self.crawl_by_web()
                
            # 规范化数据
            normalized_items = normalize_data(items, self.platform_name)
            
            # 限制最大数量
            if len(normalized_items) > self.max_items:
                normalized_items = normalized_items[:self.max_items]
                
            self.logger.info(f"成功爬取 {self.platform_name} 的 {len(normalized_items)} 条热点数据")
            
            # 保存数据
            for fmt in CrawlerConfig.OUTPUT_FORMATS:
                filename = CrawlerConfig.save_data(self.platform_name, normalized_items, fmt)
                self.logger.info(f"数据已保存到 {filename}")
                
            return normalized_items
            
        except Exception as e:
            self.logger.error(f"爬取 {self.platform_name} 数据时出错: {str(e)}", exc_info=True)
            return []
    
    def make_request(self, url, **kwargs):
        """发送HTTP请求"""
        return make_request(
            url,
            use_proxy=CrawlerConfig.USE_PROXY,
            proxy_list_path=CrawlerConfig.PROXY_LIST_PATH,
            timeout=CrawlerConfig.REQUEST_TIMEOUT,
            retry_times=CrawlerConfig.RETRY_TIMES,
            retry_delay=CrawlerConfig.RETRY_DELAY,
            **kwargs
        )
    
    def get_soup(self, url, **kwargs):
        """获取BeautifulSoup对象"""
        return get_soup(
            url,
            use_proxy=CrawlerConfig.USE_PROXY,
            proxy_list_path=CrawlerConfig.PROXY_LIST_PATH,
            timeout=CrawlerConfig.REQUEST_TIMEOUT,
            retry_times=CrawlerConfig.RETRY_TIMES,
            retry_delay=CrawlerConfig.RETRY_DELAY,
            **kwargs
        )
    
    @abstractmethod
    def crawl_by_api(self):
        """通过API爬取数据，子类必须实现"""
        pass
    
    @abstractmethod
    def crawl_by_web(self):
        """通过网页爬取数据，子类必须实现"""
        pass 