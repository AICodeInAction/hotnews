import re
import json
from crawlers.base_crawler import BaseCrawler

class ItNewsCrawler(BaseCrawler):
    """IT新闻爬虫"""
    
    def __init__(self):
        super().__init__("it_news")
    
    def crawl_by_api(self):
        """IT新闻没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取IT新闻"""
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
                if script.string and "window.__INITIAL_STATE__" in script.string:
                    try:
                        # 提取JSON字符串
                        json_str = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*});', script.string, re.DOTALL)
                        if json_str:
                            initial_state = json.loads(json_str.group(1))
                            break
                    except Exception as e:
                        self.logger.warning(f"解析IT新闻页面JSON数据失败: {str(e)}")
            
            # 如果找到JSON数据，从中提取新闻列表
            if initial_state and "information" in initial_state:
                try:
                    articles = initial_state["information"].get("informationList", [])
                    
                    for i, article in enumerate(articles):
                        try:
                            # 提取基本信息
                            title = article.get("templateMaterial", {}).get("widgetTitle", "")
                            article_id = article.get("itemId")
                            url = f"https://36kr.com/p/{article_id}"
                            
                            # 提取摘要
                            excerpt = article.get("templateMaterial", {}).get("widgetContent", "")
                            
                            # 提取发布时间
                            publish_time = article.get("templateMaterial", {}).get("publishTime", "")
                            
                            # 提取作者
                            author = article.get("templateMaterial", {}).get("authorName", "")
                            
                            # 提取封面图
                            image_url = article.get("templateMaterial", {}).get("widgetImage", "")
                            
                            item = {
                                "rank": i + 1,
                                "title": title,
                                "url": url,
                                "excerpt": excerpt,
                                "author": author,
                                "publish_time": publish_time,
                                "image_url": image_url
                            }
                            
                            items.append(item)
                            
                        except Exception as e:
                            self.logger.warning(f"处理IT新闻条目时出错: {str(e)}")
                            continue
                except Exception as e:
                    self.logger.warning(f"从JSON提取IT新闻列表失败: {str(e)}")
            
            # 如果没有找到JSON数据或解析失败，尝试通过HTML解析
            if not items:
                article_items = soup.select(".article-item")
                
                for i, article in enumerate(article_items):
                    try:
                        # 提取标题和URL
                        title_elem = article.select_one(".article-item-title")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        url = ""
                        
                        link = title_elem.select_one("a")
                        if link and link.has_attr("href"):
                            url = "https://36kr.com" + link["href"] if not link["href"].startswith("http") else link["href"]
                        
                        # 提取摘要
                        excerpt = ""
                        excerpt_elem = article.select_one(".article-item-description")
                        if excerpt_elem:
                            excerpt = excerpt_elem.text.strip()
                        
                        # 提取作者和发布时间
                        author = ""
                        publish_time = ""
                        info_elem = article.select_one(".article-item-info")
                        if info_elem:
                            info_text = info_elem.text.strip()
                            # 尝试提取作者和时间
                            author_match = re.search(r"作者[：:]\s*([^\s]+)", info_text)
                            time_match = re.search(r"(\d{4}-\d{2}-\d{2})", info_text)
                            
                            if author_match:
                                author = author_match.group(1)
                            if time_match:
                                publish_time = time_match.group(1)
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "excerpt": excerpt,
                            "author": author,
                            "publish_time": publish_time
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理IT新闻条目时出错: {str(e)}")
                        continue
            
            # 如果还没有找到结果，尝试第三种选择器
            if not items:
                news_cards = soup.select(".kr-home-flow-item")
                
                for i, card in enumerate(news_cards):
                    try:
                        # 提取标题和URL
                        title_elem = card.select_one(".title-wrapper a")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        url = ""
                        
                        if title_elem.has_attr("href"):
                            url = "https://36kr.com" + title_elem["href"] if not title_elem["href"].startswith("http") else title_elem["href"]
                        
                        # 提取摘要
                        excerpt = ""
                        excerpt_elem = card.select_one(".description-content")
                        if excerpt_elem:
                            excerpt = excerpt_elem.text.strip()
                        
                        # 提取作者
                        author = ""
                        author_elem = card.select_one(".author-name")
                        if author_elem:
                            author = author_elem.text.strip()
                        
                        # 提取发布时间
                        publish_time = ""
                        time_elem = card.select_one(".timestamp")
                        if time_elem:
                            publish_time = time_elem.text.strip()
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "excerpt": excerpt,
                            "author": author,
                            "publish_time": publish_time
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理IT新闻条目时出错: {str(e)}")
                        continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取IT新闻失败: {str(e)}")
            return [] 