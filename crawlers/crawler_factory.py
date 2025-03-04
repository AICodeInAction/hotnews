from config.config import CrawlerConfig
from crawlers.zhihu_crawler import ZhihuCrawler
from crawlers.weibo_crawler import WeiboCrawler
from crawlers.bilibili_crawler import BilibiliCrawler
from crawlers.baidu_crawler import BaiduCrawler
from crawlers.thirtysixkr_crawler import ThirtySixKrCrawler
from crawlers.douyin_crawler import DouyinCrawler
from crawlers.hupu_crawler import HupuCrawler
from crawlers.douban_crawler import DoubanCrawler
from crawlers.it_news_crawler import ITNewsCrawler
import logging

logger = logging.getLogger("HotNews.Factory")

class CrawlerFactory:
    """爬虫工厂类，管理所有平台爬虫"""
    
    _crawlers = {
        "zhihu": ZhihuCrawler,
        "weibo": WeiboCrawler,
        "bilibili": BilibiliCrawler,
        "baidu": BaiduCrawler,
        "36kr": ThirtySixKrCrawler,
        "douyin": DouyinCrawler,
        "hupu": HupuCrawler,
        "douban": DoubanCrawler,
        "it_news": ITNewsCrawler
    }
    
    @staticmethod
    def get_crawler(platform_name):
        """获取指定平台的爬虫实例"""
        if platform_name not in CrawlerFactory._crawlers:
            logger.error(f"未知平台: {platform_name}")
            return None
            
        return CrawlerFactory._crawlers[platform_name]()
    
    @staticmethod
    def get_all_crawlers():
        """获取所有平台的爬虫实例"""
        return [crawler_class() for crawler_class in CrawlerFactory._crawlers.values()]
    
    @staticmethod
    def get_enabled_crawlers():
        """获取所有启用的平台爬虫实例"""
        crawlers = []
        for platform, crawler_class in CrawlerFactory._crawlers.items():
            try:
                crawler = crawler_class()
                if crawler.enabled:
                    crawlers.append(crawler)
            except Exception as e:
                logger.error(f"初始化 {platform} 爬虫失败: {str(e)}")
                
        return crawlers
        
    @staticmethod
    def register_crawler(platform_name, crawler_class):
        """注册新的爬虫类"""
        CrawlerFactory._crawlers[platform_name] = crawler_class
        logger.info(f"已注册 {platform_name} 爬虫")
        
    @staticmethod
    def available_platforms():
        """获取所有可用的平台名称"""
        return [platform for platform, config in CrawlerConfig.PLATFORMS.items() if config.get("enabled", False)]
    
    @staticmethod
    def create_crawler(platform):
        """创建爬虫实例"""
        if platform == "zhihu":
            return ZhihuCrawler()
        elif platform == "weibo":
            return WeiboCrawler()
        elif platform == "bilibili":
            return BilibiliCrawler()
        elif platform == "baidu":
            return BaiduCrawler()
        elif platform == "36kr":
            return ThirtySixKrCrawler()
        elif platform == "douyin":
            return DouyinCrawler()
        elif platform == "hupu":
            return HupuCrawler()
        elif platform == "douban":
            return DoubanCrawler()
        elif platform == "it_news":
            return ITNewsCrawler()
        else:
            raise ValueError(f"不支持的平台: {platform}")
    
    @staticmethod
    def create_all_crawlers():
        """创建所有启用的爬虫实例"""
        crawlers = []
        for platform in CrawlerFactory.available_platforms():
            try:
                crawler = CrawlerFactory.create_crawler(platform)
                crawlers.append(crawler)
            except Exception as e:
                print(f"创建 {platform} 爬虫实例失败: {str(e)}")
        return crawlers 