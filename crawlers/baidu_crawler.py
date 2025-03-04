import re
import requests
import json
from crawlers.base_crawler import BaseCrawler

class BaiduCrawler(BaseCrawler):
    """百度热搜爬虫"""
    
    def __init__(self):
        super().__init__("baidu")
    
    def crawl_by_api(self):
        """百度没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取百度热搜"""
        try:
            # 使用requests直接获取页面内容，而不是通过BeautifulSoup
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive"
            }
            
            response = self.make_request(self.web_url, headers=headers)
            if not response:
                self.logger.error("获取网页内容失败")
                return []
                
            html_content = response.text
            
            # 尝试从HTML中提取热搜数据
            items = []
            
            # 方法1：尝试从页面中提取JSON数据
            json_data = None
            
            # 查找包含热搜数据的JSON
            json_pattern = re.search(r'<!--s-data:(.*?)-->', html_content, re.DOTALL)
            if json_pattern:
                try:
                    json_str = json_pattern.group(1).strip()
                    json_data = json.loads(json_str)
                except Exception as e:
                    self.logger.warning(f"解析JSON数据失败: {str(e)}")
            
            # 如果找到JSON数据，从中提取热搜
            if json_data and "data" in json_data and "cards" in json_data["data"]:
                for card in json_data["data"]["cards"]:
                    if "content" in card and isinstance(card["content"], list):
                        for i, item in enumerate(card["content"]):
                            try:
                                if "word" not in item:
                                    continue
                                    
                                title = item.get("word", "")
                                url = item.get("url", "")
                                hot_value = item.get("hotScore", 0)
                                
                                # 提取排名
                                rank = i + 1
                                if "index" in item and str(item["index"]).isdigit():
                                    rank = int(item["index"])
                                
                                # 提取分类
                                category = item.get("category", "")
                                
                                items.append({
                                    "rank": rank,
                                    "title": title,
                                    "url": url,
                                    "hot_value": hot_value,
                                    "category": category
                                })
                                
                            except Exception as e:
                                self.logger.warning(f"处理百度热搜条目时出错: {str(e)}")
                                continue
                
                if items:
                    return items
            
            # 方法2：直接从页面中提取热搜数据
            # 查找热搜指数和标题
            pattern = r'热搜指数\s*</div>\s*<div[^>]*>\s*([0-9,]+)\s*</div>.*?<div[^>]*class="c-single-text-ellipsis"[^>]*>(.*?)</div>'
            matches = re.findall(pattern, html_content, re.DOTALL)
            
            if not matches:
                # 尝试另一种模式
                pattern = r'热搜指数\s*</div>\s*<div[^>]*>\s*([0-9,]+)\s*</div>.*?<div[^>]*>(.*?)</div>'
                matches = re.findall(pattern, html_content, re.DOTALL)
            
            if matches:
                for i, (hot_value_str, title) in enumerate(matches):
                    try:
                        # 清理数据
                        hot_value = int(hot_value_str.replace(',', ''))
                        title = re.sub(r'<[^>]+>', '', title).strip()
                        
                        if not title:
                            continue
                            
                        # 尝试提取URL
                        url = ""
                        url_pattern = re.search(f'{re.escape(title)}.*?href="([^"]+)"', html_content, re.DOTALL)
                        if url_pattern:
                            url = url_pattern.group(1)
                        
                        items.append({
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "hot_value": hot_value,
                            "category": ""
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"处理百度热搜条目时出错: {str(e)}")
                        continue
                
                if items:
                    return items
            
            # 方法3：使用正则表达式直接提取热搜数据
            pattern = r'<div[^>]*>\s*([0-9]+)\s*</div>.*?<div[^>]*>\s*([0-9,]+)\s*</div>.*?热搜指数.*?>(.*?)<'
            matches = re.findall(pattern, html_content, re.DOTALL)
            
            if matches:
                for rank_str, hot_value_str, title in matches:
                    try:
                        # 清理数据
                        rank = int(rank_str.strip())
                        hot_value = int(hot_value_str.replace(',', ''))
                        title = re.sub(r'<[^>]+>', '', title).strip()
                        
                        if not title:
                            continue
                            
                        items.append({
                            "rank": rank,
                            "title": title,
                            "url": "",
                            "hot_value": hot_value,
                            "category": ""
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"处理百度热搜条目时出错: {str(e)}")
                        continue
            
            # 如果以上方法都失败，尝试使用BeautifulSoup解析
            if not items:
                soup = self.get_soup(self.web_url, headers=headers)
                if not soup:
                    self.logger.error("获取网页内容失败")
                    return []
                
                # 尝试查找热搜列表
                hot_items = soup.select(".hot-list li") or soup.select(".content_1YWBm .item-wrap_2oCLZ") or soup.select("[class*='content_'] [class*='item-wrap_']")
                
                for i, hot_item in enumerate(hot_items):
                    try:
                        # 提取排名
                        rank = i + 1
                        rank_elem = hot_item.select_one(".index_1Ew5p") or hot_item.select_one(".num") or hot_item.select_one("[class*='index_']")
                        if rank_elem and rank_elem.text.strip().isdigit():
                            rank = int(rank_elem.text.strip())
                        
                        # 提取标题和URL
                        title_elem = hot_item.select_one(".c-single-text-ellipsis") or hot_item.select_one(".content_1YWBm") or hot_item.select_one("[class*='content_']")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        url = ""
                        
                        link_elem = hot_item.select_one("a")
                        if link_elem and link_elem.has_attr("href"):
                            url = link_elem["href"]
                        
                        # 提取热度
                        hot_value = 0
                        hot_elem = hot_item.select_one(".hot-index_1Bl1a") or hot_item.select_one(".hot-degree") or hot_item.select_one("[class*='hot-index_']")
                        if hot_elem:
                            hot_text = hot_elem.text.strip()
                            try:
                                if "万" in hot_text:
                                    hot_value = int(float(hot_text.replace("万", "")) * 10000)
                                else:
                                    hot_value = int(re.sub(r"\D", "", hot_text))
                            except:
                                pass
                        
                        # 提取分类标签
                        category = ""
                        tag_elem = hot_item.select_one(".label_3xnwR") or hot_item.select_one(".tag") or hot_item.select_one("[class*='label_']")
                        if tag_elem:
                            category = tag_elem.text.strip()
                        
                        item = {
                            "rank": rank,
                            "title": title,
                            "url": url,
                            "hot_value": hot_value,
                            "category": category
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理百度热搜条目时出错: {str(e)}")
                        continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取百度热搜失败: {str(e)}")
            return [] 