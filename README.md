# HotNews 热点新闻聚合器

一个用于爬取中国主流平台热点新闻的Python程序，支持以下平台：

- 知乎热榜
- 36氪热门
- 百度热搜
- 哔哩哔哩（B站）热门
- 微博热搜
- 抖音热点
- 虎扑热门
- 豆瓣热门
- IT行业新闻

## 功能特点

- 支持API调用和网页爬虫双重数据获取方式
- 定时自动更新热点数据
- 支持数据导出为多种格式(JSON、CSV等)
- 可自定义爬取频率和存储策略
- 支持代理IP轮换，避免IP封禁

## 安装要求

确保您已安装Python 3.8或更高版本，然后安装依赖：

```bash
pip install -r requirements.txt
```

如果使用Selenium或Playwright爬虫，需要安装相应的驱动：

```bash
# 安装Playwright浏览器
playwright install

# 或者安装WebDriver (Selenium使用)
webdriver-manager install
```

## 使用方法

1. 基本配置:

   复制`.env.example`为`.env`并按照您的需求进行配置

2. 启动程序:

   ```bash
   python main.py
   ```

3. 定时任务模式:

   ```bash
   python scheduler.py
   ```

4. 查看结果:

   结果将保存在`data`目录下，也可通过配置输出到MongoDB或其他数据库

## 配置选项

在`.env`文件中配置以下选项：

```
# 爬虫配置
USE_PROXY=true
PROXY_LIST=./proxies.txt

# 输出配置
OUTPUT_FORMAT=json,csv
SAVE_TO_DB=true

# 定时任务配置
SCHEDULE_INTERVAL=60  # 分钟
```

## 注意事项

- 请遵守各平台的使用条款和robots.txt规则
- 爬取频率不宜过高，以免IP被封
- 商业用途请确保获得相关平台授权

## 许可证

MIT 