import re
from crawlers.base_crawler import BaseCrawler

class DoubanCrawler(BaseCrawler):
    """豆瓣热门爬虫"""
    
    def __init__(self):
        super().__init__("douban")
    
    def crawl_by_api(self):
        """豆瓣没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取豆瓣热门小组话题"""
        try:
            # 豆瓣对爬虫有较严格的限制，设置更真实的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.douban.com/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            soup = self.get_soup(self.web_url, headers=headers)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
            items = []
            
            # 查找热门小组话题
            group_items = soup.select(".channel-item")
            
            for i, group in enumerate(group_items):
                try:
                    # 提取标题和URL
                    title_elem = group.select_one(".title a")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    url = ""
                    
                    if title_elem.has_attr("href"):
                        url = title_elem["href"]
                    
                    # 提取小组名称
                    group_name = ""
                    group_elem = group.select_one(".source")
                    if group_elem:
                        group_name = group_elem.text.strip().replace("来自:", "").strip()
                    
                    # 提取回应数
                    reply_count = 0
                    reply_elem = group.select_one(".reply-num")
                    if reply_elem:
                        reply_text = reply_elem.text.strip()
                        try:
                            reply_count = int(re.search(r"(\d+)", reply_text).group(1))
                        except:
                            pass
                    
                    # 提取内容摘要
                    excerpt = ""
                    content_elem = group.select_one(".content p")
                    if content_elem:
                        excerpt = content_elem.text.strip()
                    
                    # 提取图片链接
                    image_url = ""
                    img_elem = group.select_one(".pic img")
                    if img_elem and img_elem.has_attr("src"):
                        image_url = img_elem["src"]
                    
                    item = {
                        "rank": i + 1,
                        "title": title,
                        "url": url,
                        "hot_value": reply_count,  # 以回应数作为热度值
                        "group_name": group_name,
                        "excerpt": excerpt,
                        "image_url": image_url
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理豆瓣小组话题条目时出错: {str(e)}")
                    continue
            
            # 如果上面的选择器没有找到结果，尝试另一种页面结构
            if not items:
                cards = soup.select(".channel-item")
                
                for i, card in enumerate(cards):
                    try:
                        # 提取标题和URL
                        title_elem = card.select_one("h3 a")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        url = ""
                        
                        if title_elem.has_attr("href"):
                            url = title_elem["href"]
                        
                        # 提取小组名称
                        group_name = ""
                        group_elem = card.select_one(".media__content a")
                        if group_elem:
                            group_name = group_elem.text.strip()
                        
                        # 提取摘要
                        excerpt = ""
                        excerpt_elem = card.select_one(".card-summary")
                        if excerpt_elem:
                            excerpt = excerpt_elem.text.strip()
                        
                        # 提取喜欢/回应数
                        like_count = 0
                        like_elem = card.select_one(".react-num")
                        if like_elem:
                            like_text = like_elem.text.strip()
                            try:
                                like_count = int(re.search(r"(\d+)", like_text).group(1))
                            except:
                                pass
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": url,
                            "hot_value": like_count,
                            "group_name": group_name,
                            "excerpt": excerpt
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理豆瓣热门条目时出错: {str(e)}")
                        continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取豆瓣热门失败: {str(e)}")
            return [] 