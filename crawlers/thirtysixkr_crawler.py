import re
import json
from bs4 import BeautifulSoup
from crawlers.base_crawler import BaseCrawler

class ThirtySixKrCrawler(BaseCrawler):
    """36氪热门爬虫"""
    
    def __init__(self):
        super().__init__("36kr")
    
    def crawl_by_api(self):
        """通过API爬取36氪热门"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Origin": "https://36kr.com",
                "Referer": "https://36kr.com/",
            }
            
            # 尝试多个API端点
            api_endpoints = [
                "https://36kr.com/api/newsflash/catalog",
                "https://36kr.com/api/newsflash",
                self.api_url
            ]
            
            response = None
            used_api = ""
            
            for api in api_endpoints:
                try:
                    self.logger.info(f"尝试从 {api} 获取36氪热门数据")
                    response = self.make_request(api, headers=headers)
                    if response and response.status_code == 200:
                        used_api = api
                        self.logger.info(f"成功从 {api} 获取数据")
                        break
                except Exception as e:
                    self.logger.warning(f"API请求失败 ({api}): {str(e)}")
            
            if not response:
                self.logger.error("所有API请求失败，切换到网页爬取")
                return self.crawl_by_web()
                
            data = response.json()
            items = []
            
            # 检查API响应
            if "data" in data:
                articles = []
                
                # 处理不同API返回的数据结构
                if "items" in data["data"]:
                    articles = data["data"]["items"]
                elif "newsflashes" in data["data"]:
                    articles = data["data"]["newsflashes"]
                elif isinstance(data["data"], list):
                    articles = data["data"]
                
                for i, article in enumerate(articles):
                    try:
                        title = article.get("title", "")
                        url = article.get("news_url", "") or article.get("url", "")
                        hot_value = article.get("views_count", 0) or article.get("view_count", 0) or 0
                        excerpt = article.get("description", "") or article.get("summary", "") or ""
                        publish_time = article.get("published_at", "") or article.get("published_time", "") or ""
                        author = article.get("author", {}).get("name", "") if article.get("author") else ""
                        
                        if not url.startswith("http"):
                            url = f"https://36kr.com/p/{article.get('id')}"
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "hot_value": hot_value,
                            "excerpt": excerpt,
                            "publish_time": publish_time,
                            "author": author
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理36氪文章条目时出错: {str(e)}")
                        continue
            
            if items:
                self.logger.info(f"从API获取到 {len(items)} 条36氪热门文章")
                return items
            else:
                self.logger.warning("API返回数据解析失败，切换到网页爬取")
                return self.crawl_by_web()
            
        except Exception as e:
            self.logger.error(f"通过API爬取36氪热门失败: {str(e)}")
            return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取36氪热门"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            
            # 尝试多个URL
            urls = [
                "https://36kr.com/hot-list/catalog",
                "https://36kr.com/information/web_news",
                "https://36kr.com/",
                self.web_url
            ]
            
            response = None
            used_url = ""
            
            for url in urls:
                try:
                    self.logger.info(f"尝试从 {url} 爬取36氪热门数据")
                    response = self.make_request(url, headers=headers)
                    if response and response.status_code == 200:
                        used_url = url
                        self.logger.info(f"成功从 {url} 获取数据")
                        break
                except Exception as e:
                    self.logger.warning(f"网页请求失败 ({url}): {str(e)}")
            
            if not response:
                self.logger.error("所有网页请求失败")
                return []
            
            html = response.text
            items = []
            
            # 尝试从HTML中提取JSON数据
            try:
                # 尝试多种正则模式提取JSON
                json_patterns = [
                    r'window\.initialState\s*=\s*({.*?});',
                    r'window\.__NEXT_DATA__\s*=\s*({.*?});',
                    r'window\.reactState\s*=\s*({.*?});',
                    r'"itemList":\s*(\[.*?\])',
                    r'"hotList":\s*(\[.*?\])'
                ]
                
                for pattern in json_patterns:
                    match = re.search(pattern, html, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        try:
                            data = json.loads(json_str)
                            
                            # 尝试从不同的JSON结构中提取文章数据
                            articles = []
                            
                            # 检查多种可能的数据结构
                            if "hotList" in data:
                                articles = data["hotList"]
                            elif "itemList" in data:
                                articles = data["itemList"]
                            elif "feedStream" in data and "data" in data["feedStream"]:
                                articles = data["feedStream"]["data"]
                            elif "props" in data and "pageProps" in data["props"]:
                                if "initialState" in data["props"]["pageProps"]:
                                    state = data["props"]["pageProps"]["initialState"]
                                    if "hotList" in state:
                                        articles = state["hotList"]
                                    elif "itemList" in state:
                                        articles = state["itemList"]
                            
                            if articles:
                                for i, article in enumerate(articles):
                                    try:
                                        title = article.get("title", "")
                                        url = article.get("news_url", "") or article.get("url", "") or article.get("route", "")
                                        hot_value = article.get("views_count", 0) or article.get("view_count", 0) or 0
                                        excerpt = article.get("description", "") or article.get("summary", "") or ""
                                        publish_time = article.get("published_at", "") or article.get("published_time", "") or ""
                                        author = article.get("author", {}).get("name", "") if article.get("author") else ""
                                        
                                        if not url or not url.startswith("http"):
                                            url = f"https://36kr.com/p/{article.get('id')}"
                                        
                                        item = {
                                            "rank": i + 1,
                                            "title": title,
                                            "url": url,
                                            "hot_value": hot_value,
                                            "excerpt": excerpt,
                                            "publish_time": publish_time,
                                            "author": author
                                        }
                                        
                                        items.append(item)
                                        
                                    except Exception as e:
                                        self.logger.warning(f"处理36氪文章条目时出错: {str(e)}")
                                        continue
                                
                                if items:
                                    self.logger.info(f"从JSON数据中提取到 {len(items)} 条36氪热门文章")
                                    return items
                        except json.JSONDecodeError:
                            self.logger.warning("JSON解析失败，尝试下一种模式")
                            continue
            except Exception as e:
                self.logger.warning(f"从HTML提取JSON数据失败: {str(e)}")
            
            # 如果JSON提取失败，尝试使用BeautifulSoup解析HTML
            try:
                soup = BeautifulSoup(html, "html.parser")
                
                # 尝试多种选择器
                article_selectors = [
                    "div.hotlist-item",
                    "div.kr-home-flow-item",
                    "div.article-item",
                    "div.kr-flow-article-item"
                ]
                
                for selector in article_selectors:
                    articles = soup.select(selector)
                    if articles:
                        for i, article in enumerate(articles):
                            try:
                                title_elem = article.select_one("a.title") or article.select_one("a.article-title") or article.select_one("h4")
                                title = title_elem.text.strip() if title_elem else ""
                                
                                url_elem = title_elem or article.select_one("a")
                                url = url_elem.get("href", "") if url_elem else ""
                                
                                if url and not url.startswith("http"):
                                    url = f"https://36kr.com{url}"
                                
                                excerpt_elem = article.select_one("div.summary") or article.select_one("div.description")
                                excerpt = excerpt_elem.text.strip() if excerpt_elem else ""
                                
                                author_elem = article.select_one("div.author") or article.select_one("div.user-name")
                                author = author_elem.text.strip() if author_elem else ""
                                
                                item = {
                                    "rank": i + 1,
                                    "title": title,
                                    "url": url,
                                    "hot_value": 0,
                                    "excerpt": excerpt,
                                    "author": author
                                }
                                
                                items.append(item)
                                
                            except Exception as e:
                                self.logger.warning(f"处理36氪文章HTML元素时出错: {str(e)}")
                                continue
                        
                        if items:
                            self.logger.info(f"从HTML中提取到 {len(items)} 条36氪热门文章")
                            return items
            except Exception as e:
                self.logger.error(f"使用BeautifulSoup解析HTML失败: {str(e)}")
            
            if not items:
                self.logger.error("无法从网页中提取36氪热门文章")
                return []
            
            return items
            
        except Exception as e:
            self.logger.error(f"通过网页爬取36氪热门失败: {str(e)}")
            return []
    
    def crawl(self):
        """爬取36氪热门"""
        if self.use_api:
            items = self.crawl_by_api()
        else:
            items = self.crawl_by_web()
        
        return items 