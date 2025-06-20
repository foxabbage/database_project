from bs4 import BeautifulSoup, NavigableString  # 网页解析，获取数据
import time
import random, os
import requests
from urllib.parse import quote
import re

def fetch_source_tag_and_link(url):
    """从bangumi获取作品标签
    返回一个列表"""
    print(url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://bgm.tv/anime',
        'Connection': 'keep-alive'
    }

    time.sleep(random.randint(3, 6))
    # 重试机制
    retries = 5
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                break
            elif response.status_code == 429:
                print("Too many requests. Retrying...")
                time.sleep(2 ** i)  # 指数退避
            else:
                return None
        except Exception as e:
            print(f"Error fetching tags for {url}: {e}")
            if i == retries - 1:
                return None
            time.sleep(2 ** i)

    if response.status_code != 200:
        print(f"Failed to fetch the page after {retries} retries.")
        return None

    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        # 找到 subject_tag_section 这个 div
        subject_tag_div = soup.find('div', class_='subject_tag_section')
        # 在其内部找所有 a 标签里的 span 标签文本
        tags = [a.find('span').text for a in subject_tag_div.find_all('a', class_='l meta')]
        
    except AttributeError:
        print(f"Error: No tags found for {url}")
        tags = None
    print(tags)

    try:
        li_tag = soup.find("span", class_="tip", string="官方网站: ").parent  
        
        # 3. 提取所有 <a> 的 href 属性
        links = [a["href"] for a in li_tag.find_all("a", class_="tag link thumbTipSmall")]
        print(links)
        
    except AttributeError:
        print(f"Error: No links found for {url}")
        links = None
    

    
    return tags, links
