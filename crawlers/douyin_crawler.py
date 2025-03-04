import time
import json
import re
from crawlers.base_crawler import BaseCrawler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class DouyinCrawler(BaseCrawler):
    """抖音热点爬虫"""
    
    def __init__(self):
        super().__init__("douyin")
    
    def crawl_by_api(self):
        """抖音没有公开API，调用网页爬取方法"""
        return self.crawl_by_web()
    
    def crawl_by_web(self):
        """通过网页爬取抖音热点"""
        if not self.config.get("use_selenium", False):
            self.logger.error("抖音需要使用Selenium进行爬取，请在配置中设置use_selenium=True")
            return []
            
        try:
            # 配置Selenium
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 无头模式
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={self.make_request('', headers={})}") # 使用随机UA
            
            # 初始化WebDriver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # 访问网页
            self.logger.info(f"正在访问抖音热点页面: {self.web_url}")
            driver.get(self.web_url)
            
            # 等待加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".popular-item-row"))
            )
            
            # 滚动页面以加载更多内容
            self.logger.info("滚动页面加载更多内容")
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 1000)")
                time.sleep(1)
            
            # 提取热点列表
            items = []
            
            # 尝试查找热点列表
            hot_items = driver.find_elements(By.CSS_SELECTOR, ".popular-item-row")
            
            for i, hot_item in enumerate(hot_items):
                try:
                    # 提取标题
                    title_elem = hot_item.find_element(By.CSS_SELECTOR, ".title-line")
                    title = title_elem.text.strip()
                    
                    # 提取URL
                    url = ""
                    try:
                        url_elem = hot_item.find_element(By.CSS_SELECTOR, "a")
                        url = url_elem.get_attribute("href")
                    except:
                        pass
                    
                    # 提取热度
                    hot_value = 0
                    hot_text = ""
                    try:
                        hot_elem = hot_item.find_element(By.CSS_SELECTOR, ".hot-count")
                        hot_text = hot_elem.text.strip()
                        match = re.search(r"(\d+(?:\.\d+)?)(w|万)?", hot_text)
                        if match:
                            hot_num = float(match.group(1))
                            if match.group(2) in ["w", "万"]:
                                hot_num *= 10000
                            hot_value = int(hot_num)
                    except:
                        pass
                    
                    # 提取封面图URL
                    image_url = ""
                    try:
                        img_elem = hot_item.find_element(By.CSS_SELECTOR, "img")
                        image_url = img_elem.get_attribute("src")
                    except:
                        pass
                    
                    item = {
                        "rank": i + 1,
                        "title": title,
                        "url": url,
                        "hot_value": hot_value,
                        "hot_text": hot_text,
                        "image_url": image_url
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"处理抖音热点条目时出错: {str(e)}")
                    continue
            
            # 如果第一个选择器没有找到结果，尝试另一个选择器
            if not items:
                try:
                    # 等待内容加载
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".trending-item"))
                    )
                    
                    hot_items = driver.find_elements(By.CSS_SELECTOR, ".trending-item")
                    
                    for i, hot_item in enumerate(hot_items):
                        try:
                            # 提取标题
                            title_elem = hot_item.find_element(By.CSS_SELECTOR, ".trending-item-title")
                            title = title_elem.text.strip()
                            
                            # 提取URL
                            url = ""
                            try:
                                url_elem = hot_item.find_element(By.CSS_SELECTOR, "a")
                                url = url_elem.get_attribute("href")
                            except:
                                pass
                            
                            # 提取热度
                            hot_value = 0
                            hot_text = ""
                            try:
                                hot_elem = hot_item.find_element(By.CSS_SELECTOR, ".trending-item-count")
                                hot_text = hot_elem.text.strip()
                                match = re.search(r"(\d+(?:\.\d+)?)(w|万)?", hot_text)
                                if match:
                                    hot_num = float(match.group(1))
                                    if match.group(2) in ["w", "万"]:
                                        hot_num *= 10000
                                    hot_value = int(hot_num)
                            except:
                                pass
                            
                            item = {
                                "rank": i + 1,
                                "title": title,
                                "url": url,
                                "hot_value": hot_value,
                                "hot_text": hot_text
                            }
                            
                            items.append(item)
                            
                        except Exception as e:
                            self.logger.warning(f"处理抖音热点条目时出错: {str(e)}")
                            continue
                except:
                    self.logger.warning("无法找到抖音热点列表")
            
            # 关闭浏览器
            driver.quit()
            
            return items
            
        except Exception as e:
            self.logger.error(f"爬取抖音热点失败: {str(e)}")
            return [] 