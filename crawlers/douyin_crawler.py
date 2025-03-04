import re
import json
import time
import random
import requests
import logging
from bs4 import BeautifulSoup
from crawlers.base_crawler import BaseCrawler
from fake_useragent import UserAgent

class DouyinCrawler(BaseCrawler):
    """抖音热榜爬虫"""
    
    def __init__(self):
        super().__init__("douyin")
        self.logger = logging.getLogger('HotNews')
        self.ua = UserAgent()
    
    def crawl_by_api(self):
        """通过API爬取抖音热榜"""
        try:
            # 抖音热榜API
            api_urls = [
                "https://www.douyin.com/aweme/v1/web/hot/search/list/",
                "https://aweme.snssdk.com/aweme/v1/hot/search/list/",
                "https://api.amemv.com/aweme/v1/hot/search/list/"
            ]
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Origin': 'https://www.douyin.com',
                'Referer': 'https://www.douyin.com/hot',
                'Connection': 'keep-alive',
            }
            
            # 添加随机延迟，避免被反爬
            time.sleep(random.uniform(1, 3))
            
            response = None
            for api_url in api_urls:
                try:
                    self.logger.info(f"尝试从 {api_url} 获取抖音热榜")
                    response = self.make_request(api_url, headers=headers)
                    if response:
                        break
                except Exception as e:
                    self.logger.warning(f"从 {api_url} 获取抖音热榜失败: {str(e)}")
                    continue
            
            if not response:
                self.logger.warning("API请求失败，尝试网页爬取")
                return self.crawl_by_web()
            
            try:
                data = response.json()
                
                # 检查API返回的数据结构
                if "data" not in data or "word_list" not in data.get("data", {}):
                    self.logger.warning("API返回数据结构异常，尝试网页爬取")
                    return self.crawl_by_web()
                
                hot_list = data["data"]["word_list"]
                items = []
                
                for i, item in enumerate(hot_list):
                    try:
                        # 提取标题
                        title = item.get("word", "")
                        if not title:
                            continue
                        
                        # 提取URL
                        url = f"https://www.douyin.com/search/{title}"
                        
                        # 提取热度
                        hot_value = item.get("hot_value", 0)
                        
                        # 提取标签
                        tag = ""
                        if "label" in item:
                            tag = item["label"]
                        
                        items.append({
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "hot_value": hot_value,
                            "category": tag
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"处理抖音热榜条目时出错: {str(e)}")
                        continue
                
                if items:
                    self.logger.info(f"从API获取到 {len(items)} 条抖音热榜")
                    return items
                else:
                    self.logger.warning("API返回数据为空，尝试网页爬取")
                    return self.crawl_by_web()
                
            except Exception as e:
                self.logger.error(f"解析API响应失败: {str(e)}")
                return self.crawl_by_web()
            
        except Exception as e:
            self.logger.error(f"通过API爬取抖音热榜失败: {str(e)}")
            return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取抖音热榜"""
        try:
            # 抖音热榜页面
            urls = [
                "https://www.douyin.com/hot",
                "https://www.douyin.com/discover",
                "https://www.douyin.com/channel/300201"
            ]
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Referer': 'https://www.douyin.com/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
                'Cookie': 'msToken='+self._generate_random_token(107)
            }
            
            # 添加随机延迟，避免被反爬
            time.sleep(random.uniform(1, 3))
            
            html_content = None
            for url in urls:
                try:
                    self.logger.info(f"尝试从 {url} 获取抖音热榜")
                    response = self.make_request(url, headers=headers)
                    if response:
                        html_content = response.text
                        break
                except Exception as e:
                    self.logger.warning(f"从 {url} 获取抖音热榜失败: {str(e)}")
                    continue
            
            if not html_content:
                self.logger.error("所有URL都无法获取抖音热榜")
                return []
            
            items = []
            
            # 方法1: 尝试从页面中提取JSON数据
            json_data = None
            json_patterns = [
                r'<script id="RENDER_DATA" type="application/json">(.*?)</script>',
                r'window\.__INIT_PROPS__\s*=\s*({.*?});</script>',
                r'"hotSearch":\s*({.*?}),\s*"hotVideo"'
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, html_content, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        # 抖音可能会对JSON进行URL编码
                        if '%' in json_str:
                            import urllib.parse
                            json_str = urllib.parse.unquote(json_str)
                        json_data = json.loads(json_str)
                        self.logger.info("成功从页面提取JSON数据")
                        break
                    except Exception as e:
                        self.logger.warning(f"解析JSON数据失败: {str(e)}")
            
            # 如果找到JSON数据，从中提取热榜
            if json_data:
                # 尝试多种可能的JSON结构
                hot_list = None
                
                # 尝试不同的数据路径
                data_paths = [
                    ["hotSearch", "data"],
                    ["hotSearch", "word_list"],
                    ["SSR_RENDER_DATA", "hotSearch", "data"],
                    ["SSR_RENDER_DATA", "app", "hotSearch", "data"],
                    ["state", "hotSearch", "data"]
                ]
                
                for path in data_paths:
                    current = json_data
                    valid_path = True
                    
                    for key in path:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        else:
                            valid_path = False
                            break
                    
                    if valid_path and isinstance(current, (list, dict)):
                        if isinstance(current, dict) and "word_list" in current:
                            hot_list = current["word_list"]
                        elif isinstance(current, list):
                            hot_list = current
                        break
                
                if hot_list:
                    for i, item in enumerate(hot_list):
                        try:
                            # 尝试多种可能的字段名
                            title = (item.get("word", "") or 
                                    item.get("title", "") or 
                                    item.get("content", ""))
                            
                            if not title:
                                continue
                                
                            # 提取URL
                            url = (item.get("url", "") or 
                                  item.get("link", "") or 
                                  f"https://www.douyin.com/search/{title}")
                            
                            if url and not url.startswith("http"):
                                url = "https://www.douyin.com" + url
                                
                            # 提取热度
                            hot_value = (item.get("hot_value", 0) or 
                                        item.get("view_count", 0) or 
                                        item.get("heat", 0))
                            
                            # 提取标签
                            category = (item.get("label", "") or 
                                       item.get("tag", "") or 
                                       item.get("category", ""))
                            
                            items.append({
                                "rank": i + 1,
                                "title": title,
                                "url": url,
                                "hot_value": hot_value,
                                "category": category
                            })
                            
                        except Exception as e:
                            self.logger.warning(f"处理抖音热榜条目时出错: {str(e)}")
                            continue
                    
                    if items:
                        self.logger.info(f"从JSON数据中提取到 {len(items)} 条抖音热榜")
                        return items
            
            # 方法2: 使用正则表达式直接从HTML中提取热榜数据
            pattern = r'<div[^>]*class="[^"]*hot-item[^"]*"[^>]*>.*?<div[^>]*class="[^"]*hot-item-title[^"]*"[^>]*>(.*?)</div>.*?<div[^>]*class="[^"]*hot-item-count[^"]*"[^>]*>(.*?)</div>'
            matches = re.findall(pattern, html_content, re.DOTALL)
            
            if matches:
                for i, (title_html, count_html) in enumerate(matches):
                    try:
                        # 提取标题
                        title = re.sub(r'<[^>]+>', '', title_html).strip()
                        if not title:
                            continue
                            
                        # 提取热度
                        hot_text = re.sub(r'<[^>]+>', '', count_html).strip()
                        hot_value = 0
                        match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                        if match:
                            hot_num = float(match.group(1))
                            if "万" in hot_text:
                                hot_num *= 10000
                            hot_value = int(hot_num)
                        
                        items.append({
                            "rank": i + 1,
                            "title": title,
                            "url": f"https://www.douyin.com/search/{title}",
                            "hot_value": hot_value,
                            "hot_text": hot_text
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"处理抖音热榜条目时出错: {str(e)}")
                        continue
                
                if items:
                    self.logger.info(f"从HTML正则中提取到 {len(items)} 条抖音热榜")
                    return items
            
            # 方法3: 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种选择器
            selectors = [
                ".hot-board-container .hot-board-item",  # 热榜容器
                ".hot-container .hot-item",  # 另一种热榜容器
                ".rank-content-container .rank-item",  # 排行榜容器
                ".search-card-hot-list .search-card-hot-item"  # 搜索热榜
            ]
            
            for selector in selectors:
                hot_items = soup.select(selector)
                if hot_items:
                    self.logger.info(f"使用选择器 '{selector}' 找到 {len(hot_items)} 个热榜项")
                    
                    for i, item in enumerate(hot_items):
                        try:
                            # 提取标题
                            title_elem = (item.select_one(".hot-item-title") or 
                                         item.select_one(".rank-title") or 
                                         item.select_one(".hot-item-text"))
                            
                            if not title_elem:
                                continue
                                
                            title = title_elem.text.strip()
                            if not title:
                                continue
                            
                            # 提取URL
                            url = f"https://www.douyin.com/search/{title}"
                            link_elem = item.select_one("a")
                            if link_elem and link_elem.has_attr("href"):
                                url = link_elem["href"]
                                if not url.startswith("http"):
                                    url = "https://www.douyin.com" + url
                            
                            # 提取热度
                            hot_value = 0
                            hot_text = ""
                            hot_elem = (item.select_one(".hot-item-count") or 
                                       item.select_one(".rank-count") or 
                                       item.select_one(".hot-item-num"))
                            
                            if hot_elem:
                                hot_text = hot_elem.text.strip()
                                match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                                if match:
                                    hot_num = float(match.group(1))
                                    if "万" in hot_text:
                                        hot_num *= 10000
                                    hot_value = int(hot_num)
                            
                            # 提取标签
                            category = ""
                            tag_elem = (item.select_one(".hot-item-tag") or 
                                       item.select_one(".rank-tag") or 
                                       item.select_one(".hot-item-label"))
                            
                            if tag_elem:
                                category = tag_elem.text.strip()
                            
                            items.append({
                                "rank": i + 1,
                                "title": title,
                                "url": url,
                                "hot_value": hot_value,
                                "hot_text": hot_text if 'hot_text' in locals() else "",
                                "category": category
                            })
                            
                        except Exception as e:
                            self.logger.warning(f"处理抖音热榜条目时出错: {str(e)}")
                            continue
                    
                    if items:
                        self.logger.info(f"从BeautifulSoup中提取到 {len(items)} 条抖音热榜")
                        break
            
            # 如果所有方法都失败，尝试使用备用方法
            if not items:
                # 尝试从热门搜索接口获取数据
                backup_url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
                try:
                    self.logger.info(f"尝试从备用API {backup_url} 获取抖音热榜")
                    backup_headers = {
                        'User-Agent': self.ua.random,
                        'Accept': 'application/json',
                        'Referer': 'https://www.douyin.com/hot',
                        'Cookie': 'msToken='+self._generate_random_token(107)
                    }
                    response = requests.get(backup_url, headers=backup_headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and "word_list" in data["data"]:
                            hot_list = data["data"]["word_list"]
                            for i, item in enumerate(hot_list):
                                try:
                                    title = item.get("word", "")
                                    if not title:
                                        continue
                                    
                                    items.append({
                                        "rank": i + 1,
                                        "title": title,
                                        "url": f"https://www.douyin.com/search/{title}",
                                        "hot_value": item.get("hot_value", 0),
                                        "category": item.get("label", "")
                                    })
                                except Exception as e:
                                    self.logger.warning(f"处理备用API抖音热榜条目时出错: {str(e)}")
                                    continue
                            
                            if items:
                                self.logger.info(f"从备用API获取到 {len(items)} 条抖音热榜")
                except Exception as e:
                    self.logger.warning(f"从备用API获取抖音热榜失败: {str(e)}")
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取抖音热榜失败: {str(e)}")
            return []
    
    def _generate_random_token(self, length=107):
        """生成随机token，用于模拟抖音的msToken"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        return ''.join(random.choice(chars) for _ in range(length)) 