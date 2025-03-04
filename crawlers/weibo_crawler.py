import re
from crawlers.base_crawler import BaseCrawler

class WeiboCrawler(BaseCrawler):
    """微博热搜爬虫"""
    
    def __init__(self):
        super().__init__("weibo")
    
    def crawl_by_api(self):
        """微博没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取微博热搜"""
        try:
            soup = self.get_soup(self.web_url)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
            items = []
            
            # 查找热搜列表
            hot_list = soup.select("tbody tr")
            
            for i, hot_item in enumerate(hot_list):
                try:
                    if not hot_item.select("td.td-02"):
                        continue
                        
                    rank_elem = hot_item.select_one("td.td-01")
                    main_elem = hot_item.select_one("td.td-02")
                    
                    if not main_elem:
                        continue
                        
                    # 提取标题
                    title_elem = main_elem.select_one("a")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    if not title:
                        continue
                    
                    # 提取URL
                    url = ""
                    if title_elem.has_attr("href"):
                        url = "https://s.weibo.com" + title_elem["href"]
                    
                    # 提取热度
                    hot_value = 0
                    hot_text = ""
                    hot_span = main_elem.select_one("span")
                    if hot_span:
                        hot_text = hot_span.text.strip()
                        # 提取数字
                        match = re.search(r"(\d+(?:\.\d+)?)(?:万)?", hot_text)
                        if match:
                            hot_num = float(match.group(1))
                            if "万" in hot_text:
                                hot_num *= 10000
                            hot_value = int(hot_num)
                    
                    # 提取排名
                    rank = i + 1
                    if rank_elem and rank_elem.text.strip().isdigit():
                        rank = int(rank_elem.text.strip())
                    
                    # 提取标签/分类
                    category = ""
                    label = main_elem.select_one("i")
                    if label:
                        category = label.text.strip()
                    
                    item = {
                        "rank": rank,
                        "title": title,
                        "url": url,
                        "hot_value": hot_value,
                        "hot_text": hot_text,
                        "category": category
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理微博热搜条目时出错: {str(e)}")
                    continue
            
            # 如果第一种选择器没有找到结果，尝试第二种选择器（新版微博热搜页面）
            if not items:
                hot_cards = soup.select(".card-wrap")
                
                for i, card in enumerate(hot_cards):
                    try:
                        # 提取排名
                        rank = i + 1
                        rank_elem = card.select_one(".hot-rank")
                        if rank_elem and rank_elem.text.strip().isdigit():
                            rank = int(rank_elem.text.strip())
                        
                        # 提取标题
                        title_elem = card.select_one(".hot-bd h2")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        
                        # 提取URL
                        url = ""
                        link_elem = card.select_one("a.card-wrap")
                        if link_elem and link_elem.has_attr("href"):
                            url = "https://s.weibo.com" + link_elem["href"]
                        
                        # 提取热度
                        hot_value = 0
                        hot_text = ""
                        hot_elem = card.select_one(".hot-count")
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
                        tag_elem = card.select_one(".hot-name")
                        if tag_elem:
                            category = tag_elem.text.strip()
                        
                        item = {
                            "rank": rank,
                            "title": title,
                            "url": url,
                            "hot_value": hot_value,
                            "hot_text": hot_text,
                            "category": category
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理微博热搜条目时出错: {str(e)}")
                        continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取微博热搜失败: {str(e)}")
            return [] 