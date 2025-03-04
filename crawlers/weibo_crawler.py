import re
import json
import requests
from crawlers.base_crawler import BaseCrawler
from bs4 import BeautifulSoup
import logging
import time
import random
from fake_useragent import UserAgent

class WeiboCrawler(BaseCrawler):
    """微博热搜爬虫"""
    
    def __init__(self):
        super().__init__("weibo")
        self.logger = logging.getLogger('HotNews')
        self.ua = UserAgent()
    
    def crawl_by_api(self):
        """微博没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取微博热搜"""
        try:
            # 使用requests直接获取页面内容
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Referer': 'https://weibo.com/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            
            # 添加随机延迟，避免被反爬
            time.sleep(random.uniform(1, 3))
            
            # 尝试多个URL
            urls = [
                self.web_url,
                'https://s.weibo.com/top/summary',
                'https://weibo.com/hot/search'
            ]
            
            html_content = None
            for url in urls:
                try:
                    self.logger.info(f"尝试从 {url} 获取微博热搜")
                    response = self.make_request(url, headers=headers)
                    if response:
                        html_content = response.text
                        break
                except Exception as e:
                    self.logger.warning(f"从 {url} 获取微博热搜失败: {str(e)}")
                    continue
            
            if not html_content:
                self.logger.error("所有URL都无法获取微博热搜")
                return []
            
            items = []
            
            # 方法1: 尝试从页面中提取JSON数据
            json_data = None
            json_patterns = [
                r'<script>[\s\S]*?window\._WEIBO_HOT_SEARCH_LIST_\s*=\s*({.*?});[\s\S]*?</script>',
                r'<script>[\s\S]*?var\s+hot_search\s*=\s*({.*?});[\s\S]*?</script>',
                r'<script>[\s\S]*?"hotgov":\s*({.*?}),[\s\S]*?</script>'
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, html_content)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        json_data = json.loads(json_str)
                        self.logger.info("成功从页面提取JSON数据")
                        break
                    except Exception as e:
                        self.logger.warning(f"解析JSON数据失败: {str(e)}")
            
            # 如果找到JSON数据，从中提取热搜
            if json_data:
                # 尝试多种可能的JSON结构
                hot_list = None
                
                # 结构1: data.list
                if "data" in json_data and "list" in json_data["data"]:
                    hot_list = json_data["data"]["list"]
                # 结构2: realtime
                elif "realtime" in json_data:
                    hot_list = json_data["realtime"]
                # 结构3: direct list
                elif isinstance(json_data, list):
                    hot_list = json_data
                
                if hot_list:
                    for i, hot_item in enumerate(hot_list):
                        try:
                            # 尝试多种可能的字段名
                            title = (hot_item.get("note", "") or 
                                    hot_item.get("word", "") or 
                                    hot_item.get("title", "") or 
                                    hot_item.get("content", ""))
                            
                            if not title:
                                continue
                                
                            url = (hot_item.get("url", "") or 
                                  hot_item.get("link", "") or 
                                  hot_item.get("scheme", ""))
                            
                            if url and not url.startswith("http"):
                                url = "https://s.weibo.com" + url
                                
                            hot_value = (hot_item.get("num", 0) or 
                                        hot_item.get("raw_hot", 0) or 
                                        hot_item.get("hot", 0))
                            
                            category = (hot_item.get("category", "") or 
                                       hot_item.get("label_name", "") or 
                                       hot_item.get("flag", ""))
                            
                            items.append({
                                "rank": i + 1,
                                "title": title,
                                "url": url,
                                "hot_value": hot_value,
                                "category": category
                            })
                            
                        except Exception as e:
                            self.logger.warning(f"处理微博热搜条目时出错: {str(e)}")
                            continue
                    
                    if items:
                        self.logger.info(f"从JSON数据中提取到 {len(items)} 条微博热搜")
                        return items
            
            # 方法2: 使用正则表达式直接从HTML中提取热搜数据
            pattern = r'<tr[^>]*>\s*<td[^>]*class="td-01[^"]*"[^>]*>([^<]*)</td>\s*<td[^>]*class="td-02[^"]*"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>\s*(?:<span>([^<]*)</span>)?'
            matches = re.findall(pattern, html_content, re.DOTALL)
            
            if matches:
                for rank_str, url, title, hot_text in matches:
                    try:
                        rank = int(rank_str.strip()) if rank_str.strip().isdigit() else 0
                        
                        if not title.strip():
                            continue
                            
                        if url and not url.startswith("http"):
                            url = "https://s.weibo.com" + url
                            
                        hot_value = 0
                        if hot_text:
                            match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                            if match:
                                hot_num = float(match.group(1))
                                if "万" in hot_text:
                                    hot_num *= 10000
                                hot_value = int(hot_num)
                        
                        items.append({
                            "rank": rank,
                            "title": title.strip(),
                            "url": url,
                            "hot_value": hot_value,
                            "hot_text": hot_text.strip() if hot_text else ""
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"处理微博热搜条目时出错: {str(e)}")
                        continue
                
                if items:
                    self.logger.info(f"从HTML正则中提取到 {len(items)} 条微博热搜")
                    return items
            
            # 方法3: 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种选择器
            selectors = [
                "tbody tr",  # 传统热搜页面
                ".card-wrap",  # 新版热搜页面
                ".data-list .list_a li",  # 另一种热搜页面
                ".HotList_list_3HSTeYk .HotList_item_1xZPJYE"  # 最新版热搜页面
            ]
            
            for selector in selectors:
                hot_items = soup.select(selector)
                if hot_items:
                    self.logger.info(f"使用选择器 '{selector}' 找到 {len(hot_items)} 个热搜项")
                    
                    for i, hot_item in enumerate(hot_items):
                        try:
                            # 根据不同选择器使用不同的提取逻辑
                            if selector == "tbody tr":
                                # 传统热搜页面
                                if not hot_item.select("td.td-02"):
                                    continue
                                    
                                rank_elem = hot_item.select_one("td.td-01")
                                main_elem = hot_item.select_one("td.td-02")
                                
                                if not main_elem:
                                    continue
                                    
                                title_elem = main_elem.select_one("a")
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                
                                url = ""
                                if title_elem.has_attr("href"):
                                    url = "https://s.weibo.com" + title_elem["href"] if not title_elem["href"].startswith("http") else title_elem["href"]
                                
                                hot_value = 0
                                hot_text = ""
                                hot_span = main_elem.select_one("span")
                                if hot_span:
                                    hot_text = hot_span.text.strip()
                                    match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                                    if match:
                                        hot_num = float(match.group(1))
                                        if "万" in hot_text:
                                            hot_num *= 10000
                                        hot_value = int(hot_num)
                                
                                rank = i + 1
                                if rank_elem and rank_elem.text.strip().isdigit():
                                    rank = int(rank_elem.text.strip())
                                
                                category = ""
                                label = main_elem.select_one("i")
                                if label:
                                    category = label.text.strip()
                                
                            elif selector == ".card-wrap":
                                # 新版热搜页面
                                rank = i + 1
                                rank_elem = hot_item.select_one(".hot-rank")
                                if rank_elem and rank_elem.text.strip().isdigit():
                                    rank = int(rank_elem.text.strip())
                                
                                title_elem = hot_item.select_one(".hot-bd h2") or hot_item.select_one(".card-topic-name")
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                
                                url = ""
                                link_elem = hot_item.select_one("a.card-wrap") or hot_item
                                if link_elem and link_elem.has_attr("href"):
                                    url = "https://s.weibo.com" + link_elem["href"] if not link_elem["href"].startswith("http") else link_elem["href"]
                                
                                hot_value = 0
                                hot_text = ""
                                hot_elem = hot_item.select_one(".hot-count") or hot_item.select_one(".card-hot-count")
                                if hot_elem:
                                    hot_text = hot_elem.text.strip()
                                    match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                                    if match:
                                        hot_num = float(match.group(1))
                                        if "万" in hot_text:
                                            hot_num *= 10000
                                        hot_value = int(hot_num)
                                
                                category = ""
                                tag_elem = hot_item.select_one(".hot-name") or hot_item.select_one(".card-tag")
                                if tag_elem:
                                    category = tag_elem.text.strip()
                                
                            elif selector == ".data-list .list_a li":
                                # 另一种热搜页面
                                title_elem = hot_item.select_one("a") or hot_item.select_one(".list_title")
                                
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                url = ""
                                
                                if hasattr(title_elem, "href") and title_elem["href"]:
                                    url = "https://s.weibo.com" + title_elem["href"] if not title_elem["href"].startswith("http") else title_elem["href"]
                                
                                hot_value = 0
                                hot_text = ""
                                hot_elem = hot_item.select_one(".star_num") or hot_item.select_one(".hot-index")
                                if hot_elem:
                                    hot_text = hot_elem.text.strip()
                                    match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                                    if match:
                                        hot_num = float(match.group(1))
                                        if "万" in hot_text:
                                            hot_num *= 10000
                                        hot_value = int(hot_num)
                                
                                rank = i + 1
                                category = ""
                                
                            elif selector == ".HotList_list_3HSTeYk .HotList_item_1xZPJYE":
                                # 最新版热搜页面
                                rank = i + 1
                                rank_elem = hot_item.select_one(".HotList_rank_1Xl1QJ7")
                                if rank_elem and rank_elem.text.strip().isdigit():
                                    rank = int(rank_elem.text.strip())
                                
                                title_elem = hot_item.select_one(".HotList_title_2GAq1D8")
                                if not title_elem:
                                    continue
                                    
                                title = title_elem.text.strip()
                                
                                url = ""
                                link_elem = hot_item.select_one("a")
                                if link_elem and link_elem.has_attr("href"):
                                    url = link_elem["href"] if link_elem["href"].startswith("http") else "https://s.weibo.com" + link_elem["href"]
                                
                                hot_value = 0
                                hot_text = ""
                                hot_elem = hot_item.select_one(".HotList_hot_1ARVFox")
                                if hot_elem:
                                    hot_text = hot_elem.text.strip()
                                    match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                                    if match:
                                        hot_num = float(match.group(1))
                                        if "万" in hot_text:
                                            hot_num *= 10000
                                        hot_value = int(hot_num)
                                
                                category = ""
                                tag_elem = hot_item.select_one(".HotList_label_2qxuRK9")
                                if tag_elem:
                                    category = tag_elem.text.strip()
                            
                            # 如果标题为空，跳过
                            if not title:
                                continue
                                
                            item = {
                                "rank": rank,
                                "title": title,
                                "url": url,
                                "hot_value": hot_value,
                                "hot_text": hot_text if 'hot_text' in locals() else "",
                                "category": category if 'category' in locals() else ""
                            }
                            
                            items.append(item)
                            
                        except Exception as e:
                            self.logger.warning(f"处理微博热搜条目时出错: {str(e)}")
                            continue
                    
                    if items:
                        self.logger.info(f"从BeautifulSoup中提取到 {len(items)} 条微博热搜")
                        break
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取微博热搜失败: {str(e)}")
            return [] 