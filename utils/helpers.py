import random
import time
import logging
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"crawler_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger("HotNews")

# 请求会话
session = requests.Session()
ua = UserAgent()

def get_random_user_agent():
    """获取随机User-Agent"""
    try:
        return ua.random
    except:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def get_random_proxy(proxy_list_path):
    """从代理列表中随机选择一个代理"""
    try:
        if not os.path.exists(proxy_list_path):
            logger.warning(f"代理文件 {proxy_list_path} 不存在")
            return None
            
        with open(proxy_list_path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
            
        if not proxies:
            logger.warning("代理列表为空")
            return None
            
        return random.choice(proxies)
    except Exception as e:
        logger.error(f"获取代理时出错: {str(e)}")
        return None

def make_request(url, method="GET", params=None, headers=None, proxies=None, 
                timeout=10, retry_times=3, retry_delay=2, use_proxy=False, proxy_list_path=None):
    """发送HTTP请求，支持重试和代理"""
    if headers is None:
        headers = {'User-Agent': get_random_user_agent()}
    
    for attempt in range(retry_times):
        try:
            # 如果启用代理且没有传入代理
            if use_proxy and proxies is None and proxy_list_path:
                proxy = get_random_proxy(proxy_list_path)
                if proxy:
                    proxies = {
                        'http': f'http://{proxy}',
                        'https': f'http://{proxy}'
                    }
            
            if method.upper() == "GET":
                response = session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    proxies=proxies, 
                    timeout=timeout
                )
            elif method.upper() == "POST":
                response = session.post(
                    url, 
                    json=params, 
                    headers=headers, 
                    proxies=proxies, 
                    timeout=timeout
                )
            
            # 检查是否成功
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求失败 (尝试 {attempt+1}/{retry_times}): {str(e)}")
            
            if attempt < retry_times - 1:
                time.sleep(retry_delay)
                # 如果启用代理，尝试更换代理
                if use_proxy and proxy_list_path:
                    proxies = None  # 重置代理，下次循环会重新获取
            else:
                logger.error(f"请求最终失败: {url}")
                return None

def get_soup(url, **kwargs):
    """获取页面并解析为BeautifulSoup对象"""
    response = make_request(url, **kwargs)
    if response is None:
        return None
    
    return BeautifulSoup(response.text, 'lxml')

def normalize_data(items, platform):
    """将不同平台的数据规范化为统一格式"""
    normalized = []
    
    for item in items:
        normalized_item = {
            "platform": platform,
            "timestamp": datetime.now().isoformat(),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "hot_value": item.get("hot_value", 0),
            "rank": item.get("rank", 0),
        }
        
        # 添加可能存在的其他字段
        for key in ["author", "excerpt", "category", "image_url"]:
            if key in item:
                normalized_item[key] = item[key]
                
        normalized.append(normalized_item)
        
    return normalized 