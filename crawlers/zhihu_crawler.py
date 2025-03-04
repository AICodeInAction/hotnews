import json
import re
from crawlers.base_crawler import BaseCrawler

class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""
    
    def __init__(self):
        super().__init__("zhihu")
    
    def crawl_by_api(self):
        """通过API爬取知乎热榜"""
        try:
            response = self.make_request(self.api_url)
            if not response:
                self.logger.error("API请求失败，切换到网页爬取")
                return self.crawl_by_web()
                
            data = response.json()
            items = []
            
            for i, item_data in enumerate(data.get("data", [])):
                try:
                    target = item_data.get("target", {})
                    question = target.get("question", {})
                    
                    # 获取热度值
                    detail_text = item_data.get("detail_text", "")
                    hot_value = 0
                    match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", detail_text)
                    if match:
                        hot_num = float(match.group(1))
                        if "万" in detail_text:
                            hot_num *= 10000
                        hot_value = int(hot_num)
                    
                    # 构建URL
                    url = ""
                    if question.get("url"):
                        url = "https://www.zhihu.com" + question.get("url")
                    elif question.get("id"):
                        url = f"https://www.zhihu.com/question/{question.get('id')}"
                    
                    item = {
                        "rank": i + 1,
                        "title": item_data.get("target", {}).get("title", ""),
                        "url": url,
                        "hot_value": hot_value,
                        "excerpt": target.get("excerpt", ""),
                        "category": item_data.get("category", "")
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理知乎热榜条目时出错: {str(e)}")
                    continue
                    
            return items
            
        except Exception as e:
            self.logger.error(f"通过API爬取知乎热榜失败: {str(e)}")
            return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取知乎热榜"""
        try:
            soup = self.get_soup(self.web_url)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
            items = []
            
            # 从网页中提取热榜数据
            # 使用正则表达式查找JSON数据
            script_content = ""
            scripts = soup.find_all("script")
            for script in scripts:
                content = script.string
                if content and "initialState" in content:
                    script_content = content
                    break
            
            if not script_content:
                self.logger.error("无法找到包含热榜数据的脚本")
                return []
            
            # 提取JSON数据
            json_data = None
            match = re.search(r'window\.initialState\s*=\s*({.*?})(?=;)', script_content, re.DOTALL)
            if match:
                try:
                    json_data = json.loads(match.group(1))
                except:
                    self.logger.error("解析JSON数据失败")
                    return []
            
            if not json_data:
                self.logger.error("无法解析网页中的热榜数据")
                return []
            
            # 提取热榜条目
            hot_list = json_data.get("topstory", {}).get("hotList", [])
            
            for i, item_data in enumerate(hot_list):
                try:
                    target = item_data.get("target", {})
                    
                    # 获取热度值
                    detail_text = item_data.get("detail_text", "")
                    hot_value = 0
                    match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", detail_text)
                    if match:
                        hot_num = float(match.group(1))
                        if "万" in detail_text:
                            hot_num *= 10000
                        hot_value = int(hot_num)
                    
                    # 处理URL
                    url = ""
                    question = target.get("question", {})
                    if question.get("url"):
                        url = "https://www.zhihu.com" + question.get("url")
                    elif question.get("id"):
                        url = f"https://www.zhihu.com/question/{question.get('id')}"
                    
                    item = {
                        "rank": i + 1,
                        "title": target.get("title", ""),
                        "url": url,
                        "hot_value": hot_value,
                        "excerpt": target.get("excerpt", ""),
                        "category": item_data.get("category", "")
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理知乎热榜条目时出错: {str(e)}")
                    continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"通过网页爬取知乎热榜失败: {str(e)}")
            return [] 