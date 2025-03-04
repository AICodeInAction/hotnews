#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import concurrent.futures
import os
from datetime import datetime
from tqdm import tqdm
import json
import csv

from crawlers.crawler_factory import CrawlerFactory
from config.config import CrawlerConfig, OUTPUT_FORMAT, DATA_DIR

# 导入爬虫
from crawlers.zhihu_crawler import ZhihuCrawler
from crawlers.weibo_crawler import WeiboCrawler
from crawlers.bilibili_crawler import BilibiliCrawler
from crawlers.baidu_crawler import BaiduCrawler
from crawlers.thirtysixkr_crawler import ThirtySixKrCrawler
from crawlers.douyin_crawler import DouyinCrawler
from crawlers.hupu_crawler import HupuCrawler
from crawlers.douban_crawler import DoubanCrawler
from crawlers.it_news_crawler import ITNewsCrawler

# 创建日志目录
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(logs_dir, f"main_{datetime.now().strftime('%Y%m%d')}.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("main")

def save_data(data, output_file):
    """保存数据"""
    if not data:
        logger.warning("没有数据可保存")
        return
    
    # 创建目录
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 根据文件扩展名保存数据
    if output_file.endswith(".json"):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    elif output_file.endswith(".csv"):
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    elif output_file.endswith(".xlsx"):
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_excel(output_file, index=False)
        except ImportError:
            logger.error("保存Excel格式需要安装pandas和openpyxl库")
            with open(output_file.replace(".xlsx", ".json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"数据已保存到 {output_file}")

def get_crawler(platform):
    """获取爬虫实例"""
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
        logger.error(f"不支持的平台: {platform}")
        return None

def crawl_platform(platform):
    """爬取指定平台的热门数据"""
    if platform not in CrawlerConfig.PLATFORMS:
        logger.error(f"不支持的平台: {platform}")
        return
    
    if not CrawlerConfig.PLATFORMS[platform]["enabled"]:
        logger.warning(f"平台 {platform} 已禁用")
        return
    
    logger.info(f"开始爬取 {platform} 的热门数据")
    
    # 获取爬虫实例
    crawler = get_crawler(platform)
    if not crawler:
        return
    
    # 爬取数据
    items = crawler.crawl()
    
    # 限制数量
    max_items = CrawlerConfig.PLATFORMS[platform]["max_items"]
    if len(items) > max_items:
        items = items[:max_items]
    
    # 保存数据
    config = CrawlerConfig(platform)
    output_file = config.get_output_file()
    save_data(items, output_file)
    
    logger.info(f"成功爬取 {platform} 的 {len(items)} 条热点数据")
    
    # 打印热门标题
    if items:
        logger.info(f"{platform} 热门摘要:")
        for i, item in enumerate(items[:3]):
            logger.info(f"{i+1}. {item['title']}")
    
    return items

def crawl_all_platforms(use_concurrent=True):
    """爬取所有启用的平台"""
    platforms = CrawlerFactory.available_platforms()
    results = {}
    
    if use_concurrent:
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
    print(f"数据已保存到 {DATA_DIR} 目录")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="热门数据爬虫")
    parser.add_argument("-p", "--platform", help="指定要爬取的平台", choices=list(CrawlerConfig.PLATFORMS.keys()))
    parser.add_argument("-a", "--all", help="爬取所有已启用的平台", action="store_true")
    parser.add_argument("-o", "--output", help="指定输出目录", default=DATA_DIR)
    return parser, parser.parse_args()

def main():
    """主函数"""
    parser, args = parse_args()
    
    # 设置输出目录
    global DATA_DIR
    DATA_DIR = args.output
    
    # 爬取数据
    all_items = {}
    
    if args.platform:
        items = crawl_platform(args.platform)
        if items:
            all_items[args.platform] = items
    elif args.all:
        for platform, config in CrawlerConfig.PLATFORMS.items():
            if config["enabled"]:
                items = crawl_platform(platform)
                if items:
                    all_items[platform] = items
    else:
        parser.print_help()
        return
    
    # 汇总数据
    if len(all_items) > 1:
        summary_file = os.path.join(DATA_DIR, f"summary_{datetime.now().strftime('%Y%m%d')}.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
        logger.info(f"汇总数据已保存到 {summary_file}")
        
        # 打印汇总信息
        logger.info("爬取汇总:")
        for platform, items in all_items.items():
            logger.info(f"{platform}: {len(items)} 条热点")
    
    logger.info("爬取完成")

if __name__ == "__main__":
    main() 