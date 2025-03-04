from crawlers.base_crawler import BaseCrawler

class BilibiliCrawler(BaseCrawler):
    """B站热门爬虫"""
    
    def __init__(self):
        super().__init__("bilibili")
    
    def crawl_by_api(self):
        """通过API爬取B站热门"""
        try:
            response = self.make_request(self.api_url)
            if not response:
                self.logger.error("API请求失败，切换到网页爬取")
                return self.crawl_by_web()
                
            data = response.json()
            items = []
            
            # 检查API响应
            if data.get("code") != 0:
                self.logger.error(f"B站API返回错误: {data.get('message')}")
                return self.crawl_by_web()
            
            # 获取热门视频列表
            videos = data.get("data", {}).get("list", [])
            
            for i, video in enumerate(videos):
                try:
                    item = {
                        "rank": i + 1,
                        "title": video.get("title", ""),
                        "url": f"https://www.bilibili.com/video/{video.get('bvid')}",
                        "hot_value": video.get("stat", {}).get("view", 0),
                        "author": video.get("owner", {}).get("name", ""),
                        "image_url": video.get("pic", ""),
                        "duration": video.get("duration", ""),
                        "play_count": video.get("stat", {}).get("view", 0),
                        "like_count": video.get("stat", {}).get("like", 0),
                        "comment_count": video.get("stat", {}).get("reply", 0)
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理B站热门视频条目时出错: {str(e)}")
                    continue
                    
            return items
            
        except Exception as e:
            self.logger.error(f"通过API爬取B站热门失败: {str(e)}")
            return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取B站热门"""
        try:
            soup = self.get_soup(self.web_url)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
            items = []
            
            # 找到所有视频列表项
            video_items = soup.select(".rank-item")
            
            for i, video_item in enumerate(video_items):
                try:
                    # 提取排名
                    rank_elem = video_item.select_one(".num")
                    rank = i + 1
                    if rank_elem:
                        try:
                            rank = int(rank_elem.text.strip())
                        except:
                            pass
                    
                    # 提取标题和URL
                    title_elem = video_item.select_one(".title")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    url = ""
                    if title_elem.has_attr("href"):
                        url = "https:" + title_elem["href"] if not title_elem["href"].startswith("http") else title_elem["href"]
                    
                    # 提取播放量
                    play_count = 0
                    play_elem = video_item.select_one(".detail-state .data-box:nth-child(1)")
                    if play_elem:
                        play_text = play_elem.text.strip()
                        try:
                            if "万" in play_text:
                                play_count = int(float(play_text.replace("万", "")) * 10000)
                            else:
                                play_count = int(play_text)
                        except:
                            pass
                    
                    # 提取作者
                    author = ""
                    author_elem = video_item.select_one(".up-name")
                    if author_elem:
                        author = author_elem.text.strip()
                    
                    # 提取封面图
                    image_url = ""
                    img_elem = video_item.select_one(".lazy-img img")
                    if img_elem and img_elem.has_attr("src"):
                        image_url = img_elem["src"]
                    
                    item = {
                        "rank": rank,
                        "title": title,
                        "url": url,
                        "hot_value": play_count,
                        "author": author,
                        "image_url": image_url
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理B站热门视频条目时出错: {str(e)}")
                    continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取B站热门失败: {str(e)}")
            return [] 