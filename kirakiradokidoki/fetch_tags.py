from bs4 import BeautifulSoup, NavigableString  # 网页解析，获取数据
import time
import random, os
import requests
from urllib.parse import quote
import re

from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
import time
import random

def remove_brackets(text):
    """
    去除字符串中的中文或英文括号及其中的内容
    
    参数:
        text (str): 要处理的字符串
        
    返回:
        str: 处理后的字符串
    """
    # 匹配中文括号（）及其内容
    text = re.sub(r'（[^）]*）', '', text)
    # 匹配英文括号()及其内容
    text = re.sub(r'\([^)]*\)', '', text)
    # 去除处理后的字符串中可能多余的空格
    text = ' '.join(text.split())
    return text

def fetch_tags(character_name):
    """从萌娘百科获取角色标签"""
    encoded_name = quote(character_name)
    url = f'https://zh.moegirl.org.cn/{encoded_name}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 重试机制
    for i in range(3):
        try:
            time.sleep(random.randint(2, 5))
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            break
        except Exception as e:
            if i == 2:
                print(f"Failed to fetch {character_name}: {e}")
                return None
            time.sleep(2 ** i)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    moe_points = []
    
    # 查找所有包含"萌点"的行
    for tr in soup.find_all('tr'):
        th = tr.find('th', string=re.compile(r'萌点'))
        if th is not None:
            # 获取萌点内容单元格
            content_td = tr.find('td')
            if not content_td:
                continue
                
            # 移除注释和引用标记
            for sup in content_td.find_all('sup'):
                sup.decompose()
                
            # 提取所有萌点链接
            for a in content_td.find_all('a'):
                atext = a.get('title')
                if atext:
                    moe_points.append(atext)
                
            # 处理文本中的萌点（如果有用顿号分隔的文本）
            text = content_td.get_text('、', strip=True)
            points = [p.strip() for p in text.split('、') if p.strip()]
            moe_points.extend(points)
            continue
        td = tr.find('td')
        if td is None:
            continue
        if '萌点' not in td:
            continue
            
        # 获取萌点内容单元格
        content_td = td.find_next_sibling('td')
        if not content_td:
            continue
            
        # 移除注释和引用标记
        for sup in content_td.find_all('sup'):
            sup.decompose()
            
        # 提取所有萌点链接
        for a in content_td.find_all('a'):
            moe_points.append(a.get('title'))
            
        # 处理文本中的萌点（如果有用顿号分隔的文本）
        text = content_td.get_text('、', strip=True)
        points = [p.strip() for p in text.split('、') if p.strip()]
        moe_points.extend(points)
    
    # 去重
    moe_points0 = list(set(moe_points))
    moe_points = []
    for t in moe_points0:
        t = remove_brackets(t)
        if t:
            moe_points.append(t)
    
    return moe_points if moe_points else None
    

def fetch_age(character_name):
    """从萌娘百科获取角色年龄
    返回一个字符串"""
    encoded_character_name = quote(character_name)
    url = f'https://zh.moegirl.org.cn/{encoded_character_name}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.moegirl.org.cn/',
        'Connection': 'keep-alive'
    }

    time.sleep(random.randint(5, 8))
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
            print(f"Error fetching image for {character_name}: {e}")
            if i == retries - 1:
                return None
            time.sleep(2 ** i)

    if response.status_code != 200:
        print(f"Failed to fetch the page after {retries} retries.")
        return None

    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        age_row = soup.find('th',string=re.compile(r'年龄')).parent
        age_td = age_row.find('td')
        text_nodes = [child for child in age_td.children if isinstance(child, NavigableString)]
        if text_nodes:
            age = "".join(str(node).strip() for node in text_nodes)
        else:
            age = None
    except AttributeError:
        print(f"Error: No age found for {character_name}")
        age = None
    return(age)
