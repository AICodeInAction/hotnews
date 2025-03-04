import re
import json
from crawlers.base_crawler import BaseCrawler

class Kr36Crawler(BaseCrawler):
    """36氪热门爬虫"""
    
    def __init__(self):
        super().__init__("36kr")
    
    def crawl_by_api(self):
        """36氪没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取36氪热门"""
        try:
            soup = self.get_soup(self.web_url)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
            items = []
            
            # 尝试从页面中提取JSON数据
            scripts = soup.find_all("script")
            initial_state = None
            
            for script in scripts:
                if script.string and "__NEXT_DATA__" in script.string:
                    try:
                        json_data = json.loads(script.string)
                        if "props" in json_data and "initialState" in json_data["props"]["pageProps"]:
                            initial_state = json_data["props"]["pageProps"]["initialState"]
                            break
                    except:
                        pass
            
            # 如果找到JSON数据，从中提取文章列表
            if initial_state and "hotListData" in initial_state:
                articles = initial_state["hotListData"].get("data", {}).get("hotRankingList", [])
                
                for i, article in enumerate(articles):
                    try:
                        # 提取基本信息
                        title = article.get("templateMaterial", {}).get("widgetTitle", "")
                        url = f"https://36kr.com/p/{article.get('itemId')}"
                        hot_value = article.get("templateMaterial", {}).get("hotValue", 0)
                        
                        # 提取摘要
                        excerpt = article.get("templateMaterial", {}).get("widgetContent", "")
                        
                        # 提取发布时间
                        publish_time = article.get("templateMaterial", {}).get("publishTime", "")
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "hot_value": hot_value,
                            "excerpt": excerpt,
                            "publish_time": publish_time
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理36氪文章条目时出错: {str(e)}")
                        continue
                
                return items
            
            # 如果没有找到JSON数据，尝试通过HTML解析
            article_items = soup.select(".hotlist-item-tit")
            
            for i, article in enumerate(article_items):
                try:
                    # 提取标题和URL
                    title = article.text.strip()
                    url = ""
                    
                    if article.has_attr("href"):
                        url = "https://36kr.com" + article["href"] if not article["href"].startswith("http") else article["href"]
                    
                    # 查找父元素中的热度信息
                    hot_value = 0
                    parent = article.parent
                    hot_elem = parent.select_one(".hotlist-item-hot-num")
                    if hot_elem:
                        hot_text = hot_elem.text.strip()
                        try:
                            hot_value = int(re.sub(r"\D", "", hot_text))
                        except:
                            pass
                    
                    item = {
                        "rank": i + 1,
                        "title": title,
                        "url": url,
                        "hot_value": hot_value
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理36氪文章条目时出错: {str(e)}")
                    continue
            
            # 第二种选择器，尝试新版页面结构
            if not items:
                article_cards = soup.select(".hotlist-item")
                
                for i, card in enumerate(article_cards):
                    try:
                        # 提取标题和URL
                        title_elem = card.select_one(".title-text")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        url = ""
                        
                        link_elem = card.select_one("a")
                        if link_elem and link_elem.has_attr("href"):
                            url = "https://36kr.com" + link_elem["href"] if not link_elem["href"].startswith("http") else link_elem["href"]
                        
                        # 提取热度
                        hot_value = 0
                        hot_elem = card.select_one(".hot-rank-num")
                        if hot_elem:
                            hot_text = hot_elem.text.strip()
                            try:
                                hot_value = int(re.sub(r"\D", "", hot_text))
                            except:
                                pass
                        
                        # 提取摘要
                        excerpt = ""
                        excerpt_elem = card.select_one(".desc-text")
                        if excerpt_elem:
                            excerpt = excerpt_elem.text.strip()
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "hot_value": hot_value,
                            "excerpt": excerpt
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理36氪文章条目时出错: {str(e)}")
                        continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取36氪热门失败: {str(e)}")
            return [] 