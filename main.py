#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import concurrent.futures
import os
from datetime import datetime
from tqdm import tqdm

from crawlers.crawler_factory import CrawlerFactory
from config.config import CrawlerConfig

# 设置日志
logging.basicConfig(
    level=getattr(logging, CrawlerConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(CrawlerConfig.DATA_DIR, f"hotnews_{datetime.now().strftime('%Y%m%d')}.log"))
    ]
)
logger = logging.getLogger("HotNews")

def crawl_platform(platform_name):
    """爬取指定平台的热点数据"""
    try:
        logger.info(f"开始爬取 {platform_name} 平台的热点数据")
        crawler = CrawlerFactory.get_crawler(platform_name)
        if not crawler:
            logger.error(f"找不到 {platform_name} 平台的爬虫")
            return []
            
        if not crawler.enabled:
            logger.info(f"{platform_name} 平台爬虫未启用")
            return []
            
        items = crawler.crawl()
        logger.info(f"成功爬取 {platform_name} 平台的 {len(items)} 条热点数据")
        return items
        
    except Exception as e:
        logger.error(f"爬取 {platform_name} 平台时出错: {str(e)}", exc_info=True)
        return []

def crawl_all_platforms(concurrent=True):
    """爬取所有启用的平台"""
    platforms = CrawlerFactory.available_platforms()
    results = {}
    
    if concurrent:
        # 使用线程池并发爬取
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(platforms), 5)) as executor:
            future_to_platform = {executor.submit(crawl_platform, platform): platform for platform in platforms}
            
            # 使用tqdm显示进度
            for future in tqdm(concurrent.futures.as_completed(future_to_platform), total=len(platforms), desc="爬取进度"):
                platform = future_to_platform[future]
                try:
                    results[platform] = future.result()
                except Exception as e:
                    logger.error(f"获取 {platform} 结果时出错: {str(e)}")
                    results[platform] = []
    else:
        # 顺序爬取
        for platform in tqdm(platforms, desc="爬取进度"):
            results[platform] = crawl_platform(platform)
            
    return results

def print_summary(results):
    """打印爬取结果摘要"""
    print("\n" + "=" * 50)
    print("热点新闻爬取结果摘要")
    print("=" * 50)
    
    total_items = 0
    for platform, items in results.items():
        count = len(items)
        total_items += count
        print(f"{platform.ljust(10)}: {count} 条热点")
        
        # 打印前3条热点标题
        for i, item in enumerate(items[:3]):
            print(f"  {i+1}. {item['title']}")
        print()
        
    print(f"总计爬取 {total_items} 条热点新闻")
    print("=" * 50)
    print(f"数据已保存到 {CrawlerConfig.DATA_DIR} 目录")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="热点新闻爬取工具")
    parser.add_argument("-p", "--platform", help="指定要爬取的平台，不指定则爬取所有平台")
    parser.add_argument("-s", "--sequential", action="store_true", help="顺序爬取，默认为并发爬取")
    parser.add_argument("-l", "--list", action="store_true", help="列出所有可用的平台")
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 列出所有可用平台
    if args.list:
        platforms = CrawlerFactory.available_platforms()
        print("可用的平台:")
        for platform in platforms:
            print(f"- {platform}")
        return
    
    # 爬取指定平台或所有平台
    if args.platform:
        results = {args.platform: crawl_platform(args.platform)}
    else:
        results = crawl_all_platforms(not args.sequential)
    
    # 打印摘要
    print_summary(results)

if __name__ == "__main__":
    main() 