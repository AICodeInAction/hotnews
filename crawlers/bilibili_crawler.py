import re
import json
import requests
import time
import random
from crawlers.base_crawler import BaseCrawler

class BilibiliCrawler(BaseCrawler):
    """B站热门爬虫"""
    
    def __init__(self):
        super().__init__("bilibili")
    
    def crawl_by_api(self):
        """通过API爬取B站热门"""
        try:
            # 使用更健壮的请求头，模拟浏览器行为
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Origin": "https://www.bilibili.com",
                "Referer": "https://www.bilibili.com/",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Cache-Control": "max-age=0",
            }
            
            # 生成随机Cookie值
            cookies = {
                "buvid3": f"{''.join(random.choices('0123456789ABCDEF', k=32))}-{int(time.time())}infoc",
                "_uuid": f"{''.join(random.choices('0123456789ABCDEF', k=32))}infoc",
                "b_nut": str(int(time.time())),
                "buvid4": f"{''.join(random.choices('0123456789ABCDEF', k=32))}-{int(time.time())}-{random.randint(1000, 9999)}-{random.randint(100, 999)}-infoc",
                "buvid_fp": f"{''.join(random.choices('0123456789abcdef', k=32))}",
                "CURRENT_FNVAL": "4048",
                "innersign": "0",
                "b_lsid": f"{''.join(random.choices('0123456789ABCDEF', k=32))}",
            }
            
            # 添加随机延迟，避免被反爬
            time.sleep(random.uniform(1, 3))
            
            # 尝试多个API端点
            api_endpoints = [
                "https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1",
                "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all",
                "https://api.bilibili.com/x/web-interface/index/top/feed/rcmd?fresh_type=3",
                self.api_url
            ]
            
            response = None
            used_api = ""
            
            for api in api_endpoints:
                try:
                    self.logger.info(f"尝试从 {api} 获取B站热门数据")
                    # 使用requests直接发送请求，以便添加cookies
                    response = requests.get(api, headers=headers, cookies=cookies, timeout=10)
                    if response and response.status_code == 200:
                        used_api = api
                        self.logger.info(f"成功从 {api} 获取数据")
                        break
                except Exception as e:
                    self.logger.warning(f"API请求失败 ({api}): {str(e)}")
            
            if not response:
                self.logger.error("所有API请求失败，切换到网页爬取")
                return self.crawl_by_web()
                
            data = response.json()
            items = []
            
            # 检查API响应
            if data.get("code") != 0:
                self.logger.error(f"B站API返回错误: {data.get('code')} - {data.get('message', '')}")
                # 尝试另一种API格式
                try:
                    backup_api = "https://api.bilibili.com/x/web-interface/wbi/index/top/feed/rcmd?web_location=1430650&y_num=5&fresh_type=4&feed_version=V8&fresh_idx_1h=2&fetch_row=1&fresh_idx=1&brush=1&homepage_ver=1&ps=12"
                    self.logger.info(f"尝试备用API: {backup_api}")
                    backup_response = requests.get(backup_api, headers=headers, cookies=cookies, timeout=10)
                    if backup_response.status_code == 200:
                        backup_data = backup_response.json()
                        if backup_data.get("code") == 0:
                            data = backup_data
                            used_api = backup_api
                        else:
                            return self.crawl_by_web()
                    else:
                        return self.crawl_by_web()
                except Exception as e:
                    self.logger.error(f"备用API请求失败: {str(e)}")
                    return self.crawl_by_web()
            
            # 根据不同的API端点处理数据
            if "data" in data:
                # 处理不同API返回的数据结构
                videos = []
                
                # 热门视频API
                if "item" in data.get("data", {}):
                    videos = data.get("data", {}).get("item", [])
                # 排行榜API
                elif "list" in data.get("data", {}):
                    videos = data.get("data", {}).get("list", [])
                # 推荐API
                elif "items" in data.get("data", {}):
                    videos = data.get("data", {}).get("items", [])
                # 备用结构
                elif isinstance(data.get("data", []), list):
                    videos = data.get("data", [])
                
                for i, video in enumerate(videos):
                    try:
                        # 处理不同的视频数据结构
                        title = ""
                        bvid = ""
                        author = ""
                        pic = ""
                        play_count = 0
                        like_count = 0
                        comment_count = 0
                        
                        # 标准结构
                        if "title" in video:
                            title = video.get("title", "")
                        # 推荐结构
                        elif "bvid" in video and "args" in video and "title" in video.get("args", {}):
                            title = video.get("args", {}).get("title", "")
                        
                        # 获取bvid
                        if "bvid" in video:
                            bvid = video.get("bvid", "")
                        elif "id" in video:
                            bvid = video.get("id", "")
                        
                        # 获取作者
                        if "owner" in video and "name" in video.get("owner", {}):
                            author = video.get("owner", {}).get("name", "")
                        elif "author" in video:
                            author = video.get("author", "")
                        elif "up_name" in video:
                            author = video.get("up_name", "")
                        
                        # 获取封面
                        if "pic" in video:
                            pic = video.get("pic", "")
                        elif "cover" in video:
                            pic = video.get("cover", "")
                        elif "cover_url" in video:
                            pic = video.get("cover_url", "")
                        
                        # 获取播放量
                        if "stat" in video and "view" in video.get("stat", {}):
                            play_count = video.get("stat", {}).get("view", 0)
                        elif "play" in video:
                            play_count = video.get("play", 0)
                        elif "play_count" in video:
                            play_count = video.get("play_count", 0)
                        
                        # 获取点赞量
                        if "stat" in video and "like" in video.get("stat", {}):
                            like_count = video.get("stat", {}).get("like", 0)
                        elif "like" in video:
                            like_count = video.get("like", 0)
                        
                        # 获取评论量
                        if "stat" in video and "reply" in video.get("stat", {}):
                            comment_count = video.get("stat", {}).get("reply", 0)
                        elif "reply" in video:
                            comment_count = video.get("reply", 0)
                        elif "comment_count" in video:
                            comment_count = video.get("comment_count", 0)
                        
                        # 跳过没有标题或bvid的视频
                        if not title or not bvid:
                            continue
                        
                        item = {
                            "rank": i + 1,
                            "title": title,
                            "url": f"https://www.bilibili.com/video/{bvid}",
                            "hot_value": play_count,
                            "author": author,
                            "image_url": pic,
                            "play_count": play_count,
                            "like_count": like_count,
                            "comment_count": comment_count
                        }
                        
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"处理B站热门视频条目时出错: {str(e)}")
                        continue
            
            if items:
                self.logger.info(f"从API获取到 {len(items)} 条B站热门视频")
                return items
            else:
                self.logger.warning("API返回数据解析失败，切换到网页爬取")
                return self.crawl_by_web()
            
        except Exception as e:
            self.logger.error(f"通过API爬取B站热门失败: {str(e)}")
            return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取B站热门"""
        try:
            # 使用更健壮的请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.bilibili.com/",
            }
            
            # 尝试多个网页URL
            web_urls = [
                self.web_url,
                "https://www.bilibili.com/v/popular/rank/all",
                "https://www.bilibili.com/v/popular/weekly"
            ]
            
            response = None
            for url in web_urls:
                try:
                    response = self.make_request(url, headers=headers)
                    if response and response.status_code == 200:
                        break
                except Exception as e:
                    self.logger.warning(f"网页请求失败 ({url}): {str(e)}")
            
            if not response:
                self.logger.error("获取网页内容失败")
                return []
                
            html_content = response.text
            items = []
            
            # 方法1: 尝试从页面中提取JSON数据
            json_data = None
            
            # 尝试多种JSON数据提取模式
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.__STORE__\s*=\s*({.*?});',
                r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, html_content, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        json_data = json.loads(json_str)
                        break
                    except Exception as e:
                        self.logger.warning(f"解析JSON数据失败: {str(e)}")
            
            # 如果找到JSON数据，从中提取视频列表
            if json_data:
                # 尝试多种可能的数据结构
                video_list = None
                
                # 结构1: 排行榜数据
                if "rankList" in json_data:
                    video_list = json_data.get("rankList", [])
                # 结构2: 热门视频数据
                elif "items" in json_data:
                    video_list = json_data.get("items", [])
                # 结构3: 嵌套结构
                elif "data" in json_data and "list" in json_data.get("data", {}):
                    video_list = json_data.get("data", {}).get("list", [])
                # 结构4: 更深层嵌套
                elif "props" in json_data and "pageProps" in json_data.get("props", {}):
                    page_props = json_data.get("props", {}).get("pageProps", {})
                    if "videoList" in page_props:
                        video_list = page_props.get("videoList", [])
                
                if video_list:
                    for i, video in enumerate(video_list):
                        try:
                            # 提取标题
                            title = ""
                            if "title" in video:
                                title = video.get("title", "")
                            elif "name" in video:
                                title = video.get("name", "")
                            
                            if not title:
                                continue
                            
                            # 提取URL
                            url = ""
                            if "bvid" in video:
                                url = f"https://www.bilibili.com/video/{video.get('bvid')}"
                            elif "id" in video:
                                url = f"https://www.bilibili.com/video/{video.get('id')}"
                            elif "url" in video:
                                url = video.get("url", "")
                                if url and not url.startswith("http"):
                                    url = "https:" + url
                            
                            # 提取播放量
                            play_count = 0
                            if "play" in video:
                                play_count = video.get("play", 0)
                            elif "stat" in video and "view" in video.get("stat", {}):
                                play_count = video.get("stat", {}).get("view", 0)
                            
                            # 提取作者
                            author = ""
                            if "author" in video:
                                author = video.get("author", "")
                            elif "owner" in video and "name" in video.get("owner", {}):
                                author = video.get("owner", {}).get("name", "")
                            
                            # 提取封面图
                            image_url = ""
                            if "pic" in video:
                                image_url = video.get("pic", "")
                                if image_url and not image_url.startswith("http"):
                                    image_url = "https:" + image_url
                            
                            item = {
                                "rank": i + 1,
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
                    
                    if items:
                        return items
            
            # 方法2: 使用BeautifulSoup解析HTML
            soup = self.get_soup(self.web_url, headers=headers)
            if not soup:
                self.logger.error("获取网页内容失败")
                return []
                
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
            
            # 如果第一种选择器没有找到结果，尝试第二种选择器
            if not items:
                video_items = soup.select(".video-card") or soup.select(".bili-video-card")
                
                for i, video_item in enumerate(video_items):
                    try:
                        # 提取标题和URL
                        title_elem = video_item.select_one(".title") or video_item.select_one(".bili-video-card__info--tit")
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        url = ""
                        
                        link_elem = title_elem if title_elem.name == "a" else video_item.select_one("a")
                        if link_elem and link_elem.has_attr("href"):
                            url = "https:" + link_elem["href"] if not link_elem["href"].startswith("http") else link_elem["href"]
                        
                        # 提取播放量
                        play_count = 0
                        play_elem = video_item.select_one(".play-count") or video_item.select_one(".bili-video-card__stats--item")
                        if play_elem:
                            play_text = play_elem.text.strip()
                            try:
                                if "万" in play_text:
                                    play_count = int(float(play_text.replace("万", "")) * 10000)
                                else:
                                    play_count = int(re.sub(r"\D", "", play_text))
                            except:
                                pass
                        
                        # 提取作者
                        author = ""
                        author_elem = video_item.select_one(".up-name") or video_item.select_one(".bili-video-card__info--author")
                        if author_elem:
                            author = author_elem.text.strip()
                        
                        # 提取封面图
                        image_url = ""
                        img_elem = video_item.select_one("img")
                        if img_elem:
                            if img_elem.has_attr("src"):
                                image_url = img_elem["src"]
                            elif img_elem.has_attr("data-src"):
                                image_url = img_elem["data-src"]
                        
                        item = {
                            "rank": i + 1,
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