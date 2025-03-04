import re
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
            soup = self.get_soup(self.web_url)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
            items = []
            
            # 尝试从页面中提取JSON数据
            scripts = soup.find_all("script")
            json_data = None
            
            for script in scripts:
                if script.string and "window.data" in script.string:
                    try:
                        # 提取JSON字符串
                        json_str = re.search(r'window\.data\s*=\s*({.*});', script.string, re.DOTALL)
                        if json_str:
                            json_data = json.loads(json_str.group(1))
                            break
                    except:
                        pass
            
            # 如果找到JSON数据，从中提取热搜
            if json_data and "cards" in json_data:
                for card in json_data["cards"]:
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
                
                return items
            
            # 如果没有找到JSON数据，尝试通过HTML解析
            hot_items = soup.select(".hot-list li") or soup.select(".content_1YWBm .item-wrap_2oCLZ")
            
            for i, hot_item in enumerate(hot_items):
                try:
                    # 提取排名
                    rank = i + 1
                    rank_elem = hot_item.select_one(".index_1Ew5p") or hot_item.select_one(".num")
                    if rank_elem and rank_elem.text.strip().isdigit():
                        rank = int(rank_elem.text.strip())
                    
                    # 提取标题和URL
                    title_elem = hot_item.select_one(".c-single-text-ellipsis") or hot_item.select_one(".content_1YWBm")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    url = ""
                    
                    link_elem = hot_item.select_one("a")
                    if link_elem and link_elem.has_attr("href"):
                        url = link_elem["href"]
                    
                    # 提取热度
                    hot_value = 0
                    hot_elem = hot_item.select_one(".hot-index_1Bl1a") or hot_item.select_one(".hot-degree")
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
                    tag_elem = hot_item.select_one(".label_3xnwR") or hot_item.select_one(".tag")
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