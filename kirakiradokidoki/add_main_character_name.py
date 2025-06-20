# -*- codeing = utf-8 -*-
from bs4 import BeautifulSoup  # 网页解析，获取数据
import re  # 正则表达式，进行文字匹配`
import urllib.request, urllib.error  # 制定URL，获取网页数据
import time
import random, os
from http.client import IncompleteRead, RemoteDisconnected

#subject中找人物名
findMainCharacter = re.compile(r'<span class="badge_job_tip">主角</span></small> <span class="tip">(.*?)</span><br/>')

findCover = re.compile(r'<div class="infobox">.*?<a href="(.*?)" title=.*?<ul id="infobox">', re.DOTALL) #re.DOTALL使.能匹配换行符

def askURL(url):
    while True:
        try:
            time.sleep(random.randint(5,8))
            head = { 
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 Edg/110.0.1587.41"
            }
            print(url)
            request = urllib.request.Request(url, headers=head)
            html = ""
            response = urllib.request.urlopen(request)
            html = response.read().decode("utf-8")
            return html
        except urllib.error.URLError as e:
            if hasattr(e, "code"):
                print(e.code)
            if hasattr(e, "reason"):
                print(e.reason)
            time.sleep(random.randint(10,20))
        except IncompleteRead as e:
            print("IncompleteRead error:", e)
            time.sleep(random.randint(10,20))
        except RemoteDisconnected as e:
            print("RemoteDisconnected error:", e)
            time.sleep(random.randint(10,20))
        except:
            print('unknown error')
            time.sleep(random.randint(10,20))

# 定义函数 f(content)，该函数将处理每一行第5列的内容
def f(content):
    # 在这里实现你的逻辑，例如简单的内容转换
    return content[::-1]  # 示例：将字符串反转

def getCoverAndMainCharacterName(subject_id):
    '''url = 'https://bgm.tv' + subject_id
    html = askURL(url)# 保存获取到的网页源码
    
    main_character_names = re.findall(findMainCharacter, html)
    cover_url = re.findall(findCover, html)

    return str(main_character_names), cover_url'''
    base_url = 'https://bgm.tv'
    subject_url = base_url + subject_id
    html = askURL(subject_url)

    # 先获取封面链接
    soup = BeautifulSoup(html, 'html.parser')
    try:
        cover_img_tag = soup.find('div', class_='infobox').find('a')
        # cover_url = base_url + cover_img_tag['href'] if cover_img_tag else ''# 错误的添加了base_url
        cover_url = cover_img_tag['href'] if cover_img_tag else ''
    except:
        cover_url = ''

    # 获取角色页信息
    characters_url = subject_url + '/characters'
    character_html = askURL(characters_url)
    character_soup = BeautifulSoup(character_html, 'html.parser')

    # 找所有角色div（light_odd 或 light_even）
    character_blocks = character_soup.find_all('div', class_=re.compile(r'^light_(odd|even)$'))

    main_characters = []

    for block in character_blocks:
        role_tag = block.find('span', class_='badge_job')
        if role_tag and '主角' in role_tag.text:
            # 我们从 <span class="tip">/ 国崎往人</span> 提取
            tip_span = block.find('h2').find('span', class_='tip')
            if tip_span:
                name = tip_span.text.strip().lstrip('/').strip()  # 去掉前导的 / 和空格
                main_characters.append(name)

    return str(main_characters), cover_url

