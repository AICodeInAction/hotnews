#!/usr/bin/env python
# -*- coding: utf-8 -*-

import schedule
import time
import logging
import os
from datetime import datetime

from config.config import CrawlerConfig
from main import crawl_all_platforms, print_summary

# 设置日志
logging.basicConfig(
    level=getattr(logging, CrawlerConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(CrawlerConfig.DATA_DIR, f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"))
    ]
)
logger = logging.getLogger("HotNews.Scheduler")

def job():
    """定时执行的爬取任务"""
    logger.info("开始执行定时爬取任务")
    start_time = time.time()
    
    try:
        # 爬取所有平台
        results = crawl_all_platforms(concurrent=True)
        
        # 打印摘要
        print_summary(results)
        
        # 统计耗时
        elapsed_time = time.time() - start_time
        logger.info(f"定时爬取任务完成，耗时 {elapsed_time:.2f} 秒")
        
    except Exception as e:
        logger.error(f"执行定时爬取任务时出错: {str(e)}", exc_info=True)
        
    logger.info(f"下次任务将在 {CrawlerConfig.SCHEDULE_INTERVAL} 分钟后执行")

def main():
    """主函数"""
    logger.info("热点新闻定时爬取服务已启动")
    logger.info(f"爬取间隔: {CrawlerConfig.SCHEDULE_INTERVAL} 分钟")
    
    # 立即执行一次
    job()
    
    # 设置定时任务
    schedule.every(CrawlerConfig.SCHEDULE_INTERVAL).minutes.do(job)
    
    # 运行定时任务
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("服务被用户中断")
            break
        except Exception as e:
            logger.error(f"定时任务执行出错: {str(e)}", exc_info=True)
            time.sleep(60)  # 出错后等待一分钟再继续
            
    logger.info("热点新闻定时爬取服务已停止")

if __name__ == "__main__":
    main() 