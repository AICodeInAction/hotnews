import re
import json
import time
import random
import requests
import logging
import feedparser
from bs4 import BeautifulSoup
from crawlers.base_crawler import BaseCrawler
from fake_useragent import UserAgent
from datetime import datetime

class ITNewsCrawler(BaseCrawler):
    """IT新闻爬虫"""
    
    def __init__(self):
        super().__init__("it_news")
        self.logger = logging.getLogger('HotNews')
        self.ua = UserAgent()
    
    def crawl_by_api(self):
        """通过RSS爬取IT新闻"""
        try:
            # 尝试使用RSS订阅源
            rss_urls = [
                self.api_url,
                "https://rsshub.app/36kr/news/latest",
                "https://rsshub.app/ithome/it",
                "https://rsshub.app/cnbeta"
            ]
            
            items = []
            
            for rss_url in rss_urls:
                try:
                    self.logger.info(f"尝试从RSS源 {rss_url} 获取IT新闻")
                    feed = feedparser.parse(rss_url)
                    
                    if feed.entries:
                        self.logger.info(f"成功从RSS源 {rss_url} 获取 {len(feed.entries)} 条新闻")
                        
                        for i, entry in enumerate(feed.entries):
                            try:
                                title = entry.get("title", "")
                                url = entry.get("link", "")
                                publish_time = entry.get("published", "")
                                
                                # 尝试获取摘要
                                summary = ""
                                if "summary" in entry:
                                    summary = entry.summary
                                elif "description" in entry:
                                    summary = entry.description
                                
                                # 清理HTML标签
                                if summary:
                                    summary = re.sub(r'<.*?>', '', summary)
                                
                                # 尝试获取作者
                                author = ""
                                if "author" in entry:
                                    author = entry.author
                                elif "authors" in entry and entry.authors:
                                    author = entry.authors[0].get("name", "")
                                
                                item = {
                                    "rank": i + 1,
                                    "title": title,
                                    "url": url,
                                    "hot_value": 0,
                                    "excerpt": summary,
                                    "publish_time": publish_time,
                                    "author": author
                                }
                                
                                items.append(item)
                                
                            except Exception as e:
                                self.logger.warning(f"处理RSS条目时出错: {str(e)}")
                                continue
                        
                        if items:
                            self.logger.info(f"从RSS源获取到 {len(items)} 条IT新闻")
                            return items
                    
                except Exception as e:
                    self.logger.warning(f"获取RSS源 {rss_url} 失败: {str(e)}")
                    continue
            
            if not items:
                self.logger.warning("所有RSS源获取失败，切换到网页爬取")
                return self.crawl_by_web()
            
            return items
            
        except Exception as e:
            self.logger.error(f"通过RSS爬取IT新闻失败: {str(e)}")
            return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取IT新闻"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            
            # 尝试多个IT新闻网站
            urls = [
                "https://36kr.com/information/technology",
                "https://www.ithome.com/",
                "https://www.cnbeta.com/",
                "https://www.pingwest.com/",
                self.web_url
            ]
            
            items = []
            
            for url in urls:
                try:
                    self.logger.info(f"尝试从 {url} 爬取IT新闻")
                    response = self.make_request(url, headers=headers)
                    
                    if response and response.status_code == 200:
                        html = response.text
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # 根据不同网站使用不同的选择器
                        article_elements = []
                        
                        if "36kr.com" in url:
                            article_elements = soup.select("div.article-item") or soup.select("div.kr-flow-article-item")
                        elif "ithome.com" in url:
                            article_elements = soup.select("div.block") or soup.select("div.new-list-1")
                        elif "cnbeta.com" in url:
                            article_elements = soup.select("div.item") or soup.select("div.news-list")
                        elif "pingwest.com" in url:
                            article_elements = soup.select("div.item") or soup.select("div.article-list")
                        else:
                            # 通用选择器
                            article_elements = soup.select("article") or soup.select("div.article") or soup.select("div.news-item")
                        
                        if article_elements:
                            for i, article in enumerate(article_elements):
                                try:
                                    # 提取标题和链接
                                    title_elem = article.select_one("h3") or article.select_one("h4") or article.select_one("a.title")
                                    if not title_elem:
                                        continue
                                    
                                    title = title_elem.text.strip()
                                    
                                    # 提取链接
                                    url_elem = title_elem if title_elem.name == "a" else article.select_one("a")
                                    url = url_elem.get("href", "") if url_elem else ""
                                    
                                    # 确保URL是完整的
                                    if url and not url.startswith("http"):
                                        if url.startswith("/"):
                                            base_url = "/".join(response.url.split("/")[:3])
                                            url = base_url + url
                                        else:
                                            url = response.url.rstrip("/") + "/" + url
                                    
                                    # 提取摘要
                                    excerpt_elem = article.select_one("p.desc") or article.select_one("div.summary") or article.select_one("div.description")
                                    excerpt = excerpt_elem.text.strip() if excerpt_elem else ""
                                    
                                    # 提取发布时间
                                    time_elem = article.select_one("span.time") or article.select_one("span.date") or article.select_one("time")
                                    publish_time = time_elem.text.strip() if time_elem else ""
                                    
                                    # 提取作者
                                    author_elem = article.select_one("span.author") or article.select_one("span.writer")
                                    author = author_elem.text.strip() if author_elem else ""
                                    
                                    item = {
                                        "rank": i + 1,
                                        "title": title,
                                        "url": url,
                                        "hot_value": 0,
                                        "excerpt": excerpt,
                                        "publish_time": publish_time,
                                        "author": author
                                    }
                                    
                                    items.append(item)
                                    
                                except Exception as e:
                                    self.logger.warning(f"处理文章元素时出错: {str(e)}")
                                    continue
                            
                            if items:
                                self.logger.info(f"从 {url} 获取到 {len(items)} 条IT新闻")
                                return items
                    
                except Exception as e:
                    self.logger.warning(f"爬取 {url} 失败: {str(e)}")
                    continue
            
            if not items:
                self.logger.error("无法从任何网站获取IT新闻")
                return []
            
            return items
            
        except Exception as e:
            self.logger.error(f"通过网页爬取IT新闻失败: {str(e)}")
            return []
    
    def crawl(self):
        """爬取IT新闻"""
        if self.use_api:
            items = self.crawl_by_api()
        else:
            items = self.crawl_by_web()
        
        return items 