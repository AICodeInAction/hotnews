import re
from crawlers.base_crawler import BaseCrawler

class HupuCrawler(BaseCrawler):
    """虎扑热门爬虫"""
    
    def __init__(self):
        super().__init__("hupu")
    
    def crawl_by_api(self):
        """虎扑没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取虎扑热门"""
        try:
            soup = self.get_soup(self.web_url)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
            items = []
            
            # 查找热门帖子列表
            post_items = soup.select(".bbs-sl-web-post-layout")
            
            for i, post in enumerate(post_items):
                try:
                    # 提取标题和URL
                    title_elem = post.select_one(".p-title")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    url = ""
                    
                    link = title_elem.select_one("a")
                    if link and link.has_attr("href"):
                        url = "https://bbs.hupu.com" + link["href"] if not link["href"].startswith("http") else link["href"]
                    
                    # 提取回复数
                    reply_count = 0
                    reply_elem = post.select_one(".p-reply-count")
                    if reply_elem:
                        reply_text = reply_elem.text.strip()
                        try:
                            reply_count = int(re.sub(r"\D", "", reply_text))
                        except:
                            pass
                    
                    # 提取作者
                    author = ""
                    author_elem = post.select_one(".p-author")
                    if author_elem:
                        author = author_elem.text.strip()
                    
                    # 提取帖子分类
                    category = ""
                    category_elem = post.select_one(".p-category")
                    if category_elem:
                        category = category_elem.text.strip()
                    
                    item = {
                        "rank": i + 1,
                        "title": title,
                        "url": url,
                        "hot_value": reply_count,  # 以回复数作为热度值
                        "author": author,
                        "category": category
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理虎扑帖子条目时出错: {str(e)}")
                    continue
            
            # 如果第一个选择器没有找到，尝试使用旧版页面的选择器
            if not items:
                post_items = soup.select(".bbs-sl-table-tr")
                
                for i, post in enumerate(post_items):
                    try:
                        # 提取标题和URL
                        title_elem = post.select_one(".p-title a")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        url = ""
                        
                        if title_elem.has_attr("href"):
                            url = "https://bbs.hupu.com" + title_elem["href"] if not title_elem["href"].startswith("http") else title_elem["href"]
                        
                        # 提取回复数和浏览数
                        reply_count = 0
                        view_count = 0
                        
                        reply_elem = post.select_one(".p-post-info")
                        if reply_elem:
                            info_text = reply_elem.text.strip()
                            # 尝试提取回复数和浏览数
                            reply_match = re.search(r"(\d+)回复", info_text)
                            view_match = re.search(r"(\d+)浏览", info_text)
                            
                            if reply_match:
                                reply_count = int(reply_match.group(1))
                            if view_match:
                                view_count = int(view_match.group(1))
                        
                        # 提取作者
                        author = ""
                        author_elem = post.select_one(".p-author")
                        if author_elem:
                            author = author_elem.text.strip()
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "hot_value": reply_count,  # 以回复数作为热度值
                            "reply_count": reply_count,
                            "view_count": view_count,
                            "author": author
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理虎扑帖子条目时出错: {str(e)}")
                        continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取虎扑热门失败: {str(e)}")
            return [] 