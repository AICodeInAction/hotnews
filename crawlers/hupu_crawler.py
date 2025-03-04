import re
import json
import requests
from bs4 import BeautifulSoup
from crawlers.base_crawler import BaseCrawler
import logging
import time
import random
from fake_useragent import UserAgent

class HupuCrawler(BaseCrawler):
    """虎扑热榜爬虫"""
    
    def __init__(self):
        super().__init__("hupu")
        self.logger = logging.getLogger('HotNews')
        self.ua = UserAgent()
    
    def crawl_by_api(self):
        """通过API爬取虎扑热榜"""
        try:
            # 虎扑热榜API
            api_urls = [
                "https://bbs.hupu.com/api/v1/recommend/hot/list",
                "https://bbs.hupu.com/api/v1/recommend/hot/list?page=1&limit=50",
                "https://bbs.hupu.com/api/v1/recommend/hot/list?page=1&limit=100"
            ]
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Origin': 'https://bbs.hupu.com',
                'Referer': 'https://bbs.hupu.com/all-gambia',
                'Connection': 'keep-alive',
            }
            
            # 添加随机延迟，避免被反爬
            time.sleep(random.uniform(1, 3))
            
            response = None
            for api_url in api_urls:
                try:
                    self.logger.info(f"尝试从 {api_url} 获取虎扑热榜")
                    response = self.make_request(api_url, headers=headers)
                    if response:
                        break
                except Exception as e:
                    self.logger.warning(f"从 {api_url} 获取虎扑热榜失败: {str(e)}")
                    continue
            
            if not response:
                self.logger.warning("API请求失败，尝试网页爬取")
                return self.crawl_by_web()
            
            data = response.json()
            
            # 检查API返回的数据结构
            if "data" not in data or "list" not in data["data"]:
                self.logger.warning("API返回数据结构异常，尝试网页爬取")
                return self.crawl_by_web()
            
            hot_list = data["data"]["list"]
            items = []
            
            for i, post in enumerate(hot_list):
                try:
                    # 提取标题
                    title = post.get("title", "")
                    if not title:
                        continue
                    
                    # 提取URL
                    post_id = post.get("tid", "") or post.get("id", "")
                    url = f"https://bbs.hupu.com/detail/{post_id}" if post_id else ""
                    
                    # 提取热度
                    hot_value = post.get("replies", 0) or post.get("reply_num", 0)
                    
                    # 提取作者
                    author = post.get("username", "") or post.get("author", "")
                    
                    # 提取分类
                    category = post.get("board_name", "") or post.get("forum_name", "")
                    
                    items.append({
                        "rank": i + 1,
                        "title": title,
                        "url": url,
                        "hot_value": hot_value,
                        "author": author,
                        "category": category
                    })
                    
                except Exception as e:
                    self.logger.warning(f"处理虎扑热榜条目时出错: {str(e)}")
                    continue
            
            if items:
                self.logger.info(f"从API获取到 {len(items)} 条虎扑热榜")
                return items
            else:
                self.logger.warning("API返回数据为空，尝试网页爬取")
                return self.crawl_by_web()
            
        except Exception as e:
            self.logger.error(f"通过API爬取虎扑热榜失败: {str(e)}")
            return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取虎扑热榜"""
        try:
            # 虎扑热榜页面
            urls = [
                "https://bbs.hupu.com/all-gambia",
                "https://bbs.hupu.com/topic-daily-hot",
                "https://bbs.hupu.com/all-hot"
            ]
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Referer': 'https://bbs.hupu.com/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            
            # 添加随机延迟，避免被反爬
            time.sleep(random.uniform(1, 3))
            
            html_content = None
            for url in urls:
                try:
                    self.logger.info(f"尝试从 {url} 获取虎扑热榜")
                    response = self.make_request(url, headers=headers)
                    if response:
                        html_content = response.text
                        break
                except Exception as e:
                    self.logger.warning(f"从 {url} 获取虎扑热榜失败: {str(e)}")
                    continue
            
            if not html_content:
                self.logger.error("所有URL都无法获取虎扑热榜")
                return []
            
            items = []
            
            # 方法1: 尝试从页面中提取JSON数据
            json_data = None
            json_patterns = [
                r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?});</script>',
                r'<script>window\.__STORE_DATA__\s*=\s*({.*?});</script>',
                r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, html_content, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1)
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
                    ["topicList", "list"],
                    ["pageData", "list"],
                    ["pageData", "data", "list"],
                    ["props", "pageProps", "initialData", "list"],
                    ["props", "pageProps", "initialData", "data", "list"]
                ]
                
                for path in data_paths:
                    current = json_data
                    valid_path = True
                    
                    for key in path:
                        if key in current:
                            current = current[key]
                        else:
                            valid_path = False
                            break
                    
                    if valid_path and isinstance(current, list) and len(current) > 0:
                        hot_list = current
                        break
                
                if hot_list:
                    for i, post in enumerate(hot_list):
                        try:
                            # 尝试多种可能的字段名
                            title = (post.get("title", "") or 
                                    post.get("subject", "") or 
                                    post.get("content", ""))
                            
                            if not title:
                                continue
                                
                            # 提取URL
                            url = ""
                            post_id = (post.get("tid", "") or 
                                      post.get("id", "") or 
                                      post.get("topicId", ""))
                            
                            if post_id:
                                url = f"https://bbs.hupu.com/detail/{post_id}"
                            elif "url" in post:
                                url = post["url"]
                                if not url.startswith("http"):
                                    url = "https://bbs.hupu.com" + url
                            
                            # 提取热度
                            hot_value = (post.get("replies", 0) or 
                                        post.get("reply_num", 0) or 
                                        post.get("replyCount", 0) or 
                                        post.get("views", 0))
                            
                            # 提取作者
                            author = (post.get("username", "") or 
                                     post.get("author", "") or 
                                     post.get("authorName", ""))
                            
                            # 提取分类
                            category = (post.get("board_name", "") or 
                                       post.get("forum_name", "") or 
                                       post.get("boardName", ""))
                            
                            items.append({
                                "rank": i + 1,
                                "title": title,
                                "url": url,
                                "hot_value": hot_value,
                                "author": author,
                                "category": category
                            })
                            
                        except Exception as e:
                            self.logger.warning(f"处理虎扑热榜条目时出错: {str(e)}")
                            continue
                    
                    if items:
                        self.logger.info(f"从JSON数据中提取到 {len(items)} 条虎扑热榜")
                        return items
            
            # 方法2: 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种选择器
            selectors = [
                ".bbs-sl-web-post-body .post-list .post-item",  # 新版热榜
                ".bbs-sl-table-wrapper tbody tr",  # 传统热榜
                ".bbs-index-web-post-layout .post-list .post-item",  # 另一种热榜
                ".hupu-thread-item-wrap"  # 最新版热榜
            ]
            
            for selector in selectors:
                post_items = soup.select(selector)
                if post_items:
                    self.logger.info(f"使用选择器 '{selector}' 找到 {len(post_items)} 个热榜项")
                    
                    for i, post in enumerate(post_items):
                        try:
                            # 根据不同选择器使用不同的提取逻辑
                            if selector == ".bbs-sl-web-post-body .post-list .post-item":
                                # 新版热榜
                                title_elem = post.select_one(".post-title a")
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                
                                url = ""
                                if title_elem.has_attr("href"):
                                    url = title_elem["href"]
                                    if not url.startswith("http"):
                                        url = "https://bbs.hupu.com" + url
                                
                                hot_value = 0
                                reply_elem = post.select_one(".post-reply-count")
                                if reply_elem:
                                    reply_text = reply_elem.text.strip()
                                    match = re.search(r"(\d+)", reply_text)
                                    if match:
                                        hot_value = int(match.group(1))
                                
                                author = ""
                                author_elem = post.select_one(".post-author")
                                if author_elem:
                                    author = author_elem.text.strip()
                                
                                category = ""
                                category_elem = post.select_one(".post-forum")
                                if category_elem:
                                    category = category_elem.text.strip()
                                
                            elif selector == ".bbs-sl-table-wrapper tbody tr":
                                # 传统热榜
                                title_elem = post.select_one("td.p_title a")
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                
                                url = ""
                                if title_elem.has_attr("href"):
                                    url = title_elem["href"]
                                    if not url.startswith("http"):
                                        url = "https://bbs.hupu.com" + url
                                
                                hot_value = 0
                                reply_elem = post.select_one("td.p_reply")
                                if reply_elem:
                                    reply_text = reply_elem.text.strip()
                                    match = re.search(r"(\d+)", reply_text)
                                    if match:
                                        hot_value = int(match.group(1))
                                
                                author = ""
                                author_elem = post.select_one("td.p_author")
                                if author_elem:
                                    author = author_elem.text.strip()
                                
                                category = ""
                                category_elem = post.select_one("td.p_forum")
                                if category_elem:
                                    category = category_elem.text.strip()
                                
                            elif selector == ".bbs-index-web-post-layout .post-list .post-item":
                                # 另一种热榜
                                title_elem = post.select_one(".post-title a")
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                
                                url = ""
                                if title_elem.has_attr("href"):
                                    url = title_elem["href"]
                                    if not url.startswith("http"):
                                        url = "https://bbs.hupu.com" + url
                                
                                hot_value = 0
                                reply_elem = post.select_one(".post-reply-count")
                                if reply_elem:
                                    reply_text = reply_elem.text.strip()
                                    match = re.search(r"(\d+)", reply_text)
                                    if match:
                                        hot_value = int(match.group(1))
                                
                                author = ""
                                author_elem = post.select_one(".post-author")
                                if author_elem:
                                    author = author_elem.text.strip()
                                
                                category = ""
                                category_elem = post.select_one(".post-forum")
                                if category_elem:
                                    category = category_elem.text.strip()
                                
                            elif selector == ".hupu-thread-item-wrap":
                                # 最新版热榜
                                title_elem = post.select_one(".thread-title a")
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                
                                url = ""
                                if title_elem.has_attr("href"):
                                    url = title_elem["href"]
                                    if not url.startswith("http"):
                                        url = "https://bbs.hupu.com" + url
                                
                                hot_value = 0
                                reply_elem = post.select_one(".thread-reply-num")
                                if reply_elem:
                                    reply_text = reply_elem.text.strip()
                                    match = re.search(r"(\d+)", reply_text)
                                    if match:
                                        hot_value = int(match.group(1))
                                
                                author = ""
                                author_elem = post.select_one(".thread-author-name")
                                if author_elem:
                                    author = author_elem.text.strip()
                                
                                category = ""
                                category_elem = post.select_one(".thread-forum-name")
                                if category_elem:
                                    category = category_elem.text.strip()
                            
                            # 如果标题为空，跳过
                            if not title:
                                continue
                                
                            items.append({
                                "rank": i + 1,
                                "title": title,
                                "url": url,
                                "hot_value": hot_value,
                                "author": author,
                                "category": category
                            })
                            
                        except Exception as e:
                            self.logger.warning(f"处理虎扑热榜条目时出错: {str(e)}")
                            continue
                    
                    if items:
                        self.logger.info(f"从BeautifulSoup中提取到 {len(items)} 条虎扑热榜")
                        break
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取虎扑热榜失败: {str(e)}")
            return [] 