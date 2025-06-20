# -*- codeing = utf-8 -*-
from bs4 import BeautifulSoup  # 网页解析，获取数据
import re  # 正则表达式，进行文字匹配`
import urllib.request, urllib.error  # 制定URL，获取网页数据
import mysql.connector  # MySQL数据库连接
from mysql.connector import Error
import time
import random, os
from http.client import IncompleteRead, RemoteDisconnected
import kirakiradokidoki.add_main_character_name as add_main_character_name
import requests
from urllib.parse import quote
from datetime import datetime
import kirakiradokidoki.fetch_tags as fetch_tags
import kirakiradokidoki.fetch_source_tag_and_link as fetch_source_tag_and_link

# 正则表达式模式
findTitle = re.compile(r'<a class="l" href=.*>(.*?)</a>')  # 匹配标题
findRating = re.compile(r'<span class.*"fade">(.*?)<')  # 匹配评分
findJudge = re.compile(r'<span class.*"tip_j">\((.*?)人评分\)<')  # 匹配评价人数
findTip = re.compile(r'<div class="subject_tag_section">.*?<div class="inner">(.*?)</div>', re.S)  # 匹配标签区域
findTag = re.compile(r'<a href="/anime/tag/[^"]*" class="l meta"><span>(.*?)</span>')  # 匹配前5个标签
findStudio = re.compile(r'<span class="tip">动画制作: </span><a[^>]*>(.*?)</a>')  # 匹配制作公司
findAuthor = re.compile(r'<span class="tip">导演: </span><a[^>]*>(.*?)</a>')  # 匹配导演
findReleaseDate = re.compile(r'<span class="tip">放送开始: </span>(.*?)年(.*?)月(.*?)日')  # 匹配放送开始日期
findDescription = re.compile(r'<div id="subject_summary"[^>]*>(.*?)</div>', re.S)  # 匹配简介
findSubject = re.compile(r'<a class="l" href="(.*?)">')  # 匹配subject链接
findRank = re.compile(r'<span class="rank">(.*?)</span>')  # 匹配排名

def askURL(url):
    """获取网页内容"""
    head = {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
    }
    request = urllib.request.Request(url, headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(request)
        html = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    except IncompleteRead as e:
        print(f"IncompleteRead error: {e}")
        time.sleep(5)  # 等待5秒后重试
        return askURL(url)  # 递归重试
    except RemoteDisconnected as e:
        print(f"RemoteDisconnected error: {e}")
        time.sleep(5)  # 等待5秒后重试
        return askURL(url)  # 递归重试
    return html

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yyh2005',
    'database': 'anime'
}

# 网站ID常量
WEBSITE_BANGUMI = 1
WEBSITE_MOEGIRL = 2

def fetch_image_src(character_name):
    """从萌娘百科获取角色图片URL"""
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
    
    infobox_image_container = soup.find('tr', class_='infobox-image-container')
    if infobox_image_container is None:
        print(f"Error: No image container found for {character_name}")
        return None
    
    img_tag = infobox_image_container.find('img')
    if img_tag is None:
        print(f"Error: No image tag found for {character_name}")
        return None
    
    return img_tag.get('src')

def extract_date_from_tags(html):
    """从HTML中提取日期"""
    match = re.search(findReleaseDate, html)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day).date()
    return None

def extract_studio_from_tags(html):
    """从HTML中提取制作公司"""
    match = re.search(findStudio, html)
    return match.group(1) if match else None

def extract_author_from_tags(html):
    """从HTML中提取导演"""
    match = re.search(findAuthor, html)
    return match.group(1) if match else None

def extract_description_from_tags(html):
    """从HTML中提取简介"""
    match = re.search(findDescription, html)
    if match:
        # 移除HTML标签和多余的空白
        desc = re.sub(r'<br\s*/?>', '\n', match.group(1))
        desc = re.sub(r'<[^>]+>', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        return desc
    return None

def extract_tags_from_html(html):
    """从HTML中提取前5个标签"""
    tags = []
    tag_matches = re.finditer(findTag, html)
    for i, match in enumerate(tag_matches):
        if i >= 5:  # 只取前5个标签
            break
        tags.append(match.group(1))
    return tags

def getPageData(baseurl):
    """获取页面数据"""
    datalist = []  #用来存储爬取的网页信息
    html = askURL(baseurl)  # 保存获取到的网页源码
    if not html:  # 如果获取页面失败，返回空列表
        return datalist
        
    # 2.逐一解析数据
    soup = BeautifulSoup(html, "html.parser")

    for item in soup.find_all('div', class_="inner"):  # 查找符合要求的字符串
        data = []  # 保存信息
        item = str(item)

        # 获取标题
        titles = re.findall(findTitle, item)   
        if len(titles) == 0:  # 无数据
            continue
        data.append(titles)

        # 获取排名
        rank = re.findall(findRank, item)
        data.append(rank)

        # 获取评分
        rating = re.findall(findRating, item)
        data.append(rating)

        # 获取评价人数
        judgeNum = re.findall(findJudge, item)
        data.append(judgeNum)

        # 获取标签
        #tags = []
        #tag_matches = re.finditer(findTag, item)
        #for i, match in enumerate(tag_matches):
            #if i >= 5:  # 只取前5个标签
                #break
            #tags.append(match.group(1))
        #data.append([','.join(tags)] if tags else [" "])

        # 获取subject链接
        subject = re.findall(findSubject, item)
        data.append(subject)

        # 获取详细信息
        if subject:
            detail_url = f"https://bgm.tv{subject[0]}"
            detail_html = askURL(detail_url)
            if detail_html:
                # 提取制作公司
                studio_match = re.search(findStudio, detail_html)
                studio = studio_match.group(1) if studio_match else None
                data.append(studio)

                # 提取导演
                author_match = re.search(findAuthor, detail_html)
                author = author_match.group(1) if author_match else None
                data.append(author)

                # 提取发布日期
                date_match = re.search(findReleaseDate, detail_html)
                if date_match:
                    year, month, day = map(int, date_match.groups())
                    release_date = datetime(year, month, day).date()
                    data.append(release_date)
                else:
                    data.append(None)

                # 提取简介
                desc_match = re.search(findDescription, detail_html)
                if desc_match:
                    desc = re.sub(r'<br\s*/?>', '\n', desc_match.group(1))
                    desc = re.sub(r'<[^>]+>', '', desc)
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    data.append(desc)
                else:
                    data.append(None)

        datalist.append(data)

    return datalist

def getYearData(year, baseurl, search_page_num):
    """获取指定年份的数据"""
    datalist = []
    for page in range(1, search_page_num + 1):
        url = baseurl.format(str(year), str(page))
        # 爬取网页
        datalist += getPageData(url)
    return datalist
    
def create_database_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_tables(connection):
    try:
        cursor = connection.cursor()
        
        # 创建Website表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Website (
                website_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                base_url VARCHAR(255) NOT NULL,
                description TEXT
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建Source表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Source (
                source_id INT AUTO_INCREMENT PRIMARY KEY,
                source_type ENUM('animation', 'novel', 'manga', 'game') DEFAULT 'animation' NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                author VARCHAR(100),
                studio VARCHAR(100),
                release_date DATE,
                status ENUM('not_released', 'ongoing', 'ended'),
                UNIQUE(source_type, name)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建SourceWebpage表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SourceWebpage (
                webpage_id INT AUTO_INCREMENT PRIMARY KEY,
                website_id INT NOT NULL,
                source_id INT NOT NULL,
                url VARCHAR(255) NOT NULL UNIQUE,
                http_status_code SMALLINT NOT NULL,
                crawl_time DATETIME NOT NULL,
                last_modified DATETIME,
                FOREIGN KEY (website_id) REFERENCES Website(website_id) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES Source(source_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建SourceImage表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SourceImage (
                image_id INT AUTO_INCREMENT PRIMARY KEY,
                url VARCHAR(255) NOT NULL UNIQUE,
                file_size INT,
                format VARCHAR(20),
                is_downloaded BOOLEAN DEFAULT FALSE,
                local_path VARCHAR(255),
                source_id INT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES Source(source_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建SourceTag表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SourceTag (
                tag_id INT AUTO_INCREMENT PRIMARY KEY,
                tag VARCHAR(200) NOT NULL UNIQUE,
                num INT NOT NULL DEFAULT 1
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建SourceTagRelation表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SourceTagRelation (
                tag_id INT NOT NULL,
                source_id INT NOT NULL,
                PRIMARY KEY (source_id, tag_id),
                FOREIGN KEY (tag_id) REFERENCES SourceTag(tag_id) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES Source(source_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建Role表 (原characters表)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Role (
                role_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(30) NOT NULL,
                gender ENUM('male', 'female', 'unknown') NOT NULL DEFAULT 'unknown',
                description TEXT,
                birthday DATE,
                voice_actor VARCHAR(20)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleTag (
                tag_id INT PRIMARY KEY AUTO_INCREMENT, 
                tag CHAR(20) NOT NULL UNIQUE,
                num INT NOT NULL
            )CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleTagRelation(
                tag_id INT NOT NULL,
                role_id INT NOT NULL,
                PRIMARY KEY (role_id, tag_id),
                FOREIGN KEY (tag_id) REFERENCES RoleTag(tag_id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES Role(role_id) ON DELETE CASCADE
            )
        """)

        # 创建RoleSourceRelation表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleSourceRelation (
                role_id INT NOT NULL,
                source_id INT NOT NULL,
                PRIMARY KEY (role_id, source_id),
                FOREIGN KEY (role_id) REFERENCES Role(role_id) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES Source(source_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建RoleWebpage表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleWebpage (
                webpage_id INT AUTO_INCREMENT PRIMARY KEY,
                website_id INT NOT NULL,
                role_id INT NOT NULL,
                url VARCHAR(255) NOT NULL UNIQUE,
                http_status_code SMALLINT NOT NULL,
                crawl_time DATETIME NOT NULL,
                last_modified DATETIME,
                FOREIGN KEY (website_id) REFERENCES Website(website_id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES Role(role_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建RoleImage表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleImage (
                image_id INT AUTO_INCREMENT PRIMARY KEY,
                image_url VARCHAR(255) NOT NULL UNIQUE,
                file_size INT,
                format VARCHAR(20),
                is_downloaded BOOLEAN DEFAULT FALSE,
                local_path VARCHAR(255),
                role_id INT NOT NULL,
                FOREIGN KEY (role_id) REFERENCES Role(role_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        # 外部链接
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ExternalLinks (
                link_id INT AUTO_INCREMENT PRIMARY KEY, 
                title VARCHAR(64) NOT NULL,
                original_url VARCHAR(255) NOT NULL UNIQUE,
                publisher VARCHAR(255)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LinksOnPage (
                source_id INT NOT NULL,
                link_id INT NOT NULL,
                PRIMARY KEY (source_id, link_id),
                FOREIGN KEY (source_id) REFERENCES Source(source_id) ON DELETE CASCADE,
                FOREIGN KEY (link_id) REFERENCES ExternalLinks(link_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        # 插入网站数据
        cursor.execute("""
            INSERT IGNORE INTO Website (website_id, name, base_url, description) 
            VALUES 
            (1, 'Bangumi', 'https://bgm.tv', 'Bangumi 番组计划'),
            (2, 'Moegirl', 'https://zh.moegirl.org.cn', '萌娘百科')
        """)
        
        connection.commit()
        print("Tables created successfully")
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
'''
def process_tags(tags_str, cursor, source_id):
    """处理标签并保存到数据库"""
    if not tags_str:
        return
    
    # 分割标签
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    print(tags)
    
    for tag in tags:
        # 插入或更新标签
        cursor.execute("""
            INSERT INTO SourceTag (tag, num) 
            VALUES (%s, 1)
            ON DUPLICATE KEY UPDATE num = num + 1
        """, (tag,))
        
        # 获取标签ID
        cursor.execute("SELECT tag_id FROM SourceTag WHERE tag = %s", (tag,))
        tag_id = cursor.fetchone()[0]
        
        # 创建标签关系
        cursor.execute("""
            INSERT IGNORE INTO SourceTagRelation (tag_id, source_id)
            VALUES (%s, %s)
        """, (tag_id, source_id))
'''
def get_character_info(character, bangumi_url):
    # get gender, description, birthday, voice_actor
    gender = None
    description = None
    birthday = None
    voice_actor = None

    characters_url = bangumi_url + '/characters'
    characters_html = askURL(characters_url)
    
    # 查找角色URL
    find_character_url = fr'<h2><a\s+href="(/character/\d+)"\s+class="l">[^<]*</a>\s*<span\s+class="tip">\s*/\s*{re.escape(character)}</span></h2>'
    match = re.search(find_character_url, characters_html)
    
    if not match:
        print(f"未找到角色: {character}")
        return gender, description, birthday, voice_actor  # 未找到角色时直接返回
    
    character_url_suffix = match.group(1)
    print(f"找到角色URL: {character_url_suffix}")
    
    # 获取角色详情页
    character_url = f"https://bgm.tv" + character_url_suffix
    character_html = askURL(character_url)
    
    # 提取性别
    find_gender = r'<li\s+class=""><span\s+class="tip">性别:\s*</span>([^<]+)</li>'
    match = re.search(find_gender, character_html)
    if match:
        gender_to_choose = match.group(1)
        if gender_to_choose == "女":
            gender = 'female'
        elif gender_to_choose == "男":
            gender = 'male'
        else:
            gender = 'unknown'
    
    # 提取生日
    find_birth = r'<li\s+class=""><span\s+class="tip">生日:\s*</span>(\d+月\d+日)</li>'
    match = re.search(find_birth, character_html)
    if match:
        birthday_text = match.group(1)  # 提取 "7月23日"
        try:
            # 解析为日期对象（年份设为默认值 2000）
            date_obj = datetime.strptime(birthday_text, "%m月%d日")
            # 格式化为 MySQL DATE 格式（年默认设为 2000）
            birthday = date_obj.strftime("2000-%m-%d")
        except ValueError:
            print(f"生日格式解析错误: {birthday_text}")
    
    # 提取描述
    find_description = r'<div class="detail">([\s\S]*?)</div>'
    match = re.search(find_description, character_html)
    if match:
        description = match.group(1).strip()  # 获取匹配的内容并去除首尾空白
    
    # 提取声优
    find_voice_actor = r'<div class="inner">\s*<h3><a\s+class="l"\s+href="/person/\d+">([^<]+)</a></h3>'
    match = re.search(find_voice_actor, character_html)
    if match:
        voice_actor = match.group(1)

    soup = BeautifulSoup(character_html, "html.parser")

    # 2. 定位 <img> 标签，提取 src 属性
    img_tag = soup.find("img", class_="cover")  # 用 class 定位 <img>
    img_src = img_tag["src"] if img_tag else None
    
    return gender, description, birthday, voice_actor, img_src
    


def saveData(datalist, connection, year):
    print(f"Saving data for year {year}...")
    try:
        cursor = connection.cursor()
        
        for data in datalist:
            print("Processing data item:", data)  # Debug print
            
            # 准备数据
            title = data[0][0] if data[0] else ""  # 获取标题
            # tags = data[4][0] if data[4] and len(data[4]) > 0 else " "  # 获取标签
            studio = data[5] if len(data) > 5 else None  # 获取制作公司
            author = data[6] if len(data) > 6 else None  # 获取导演
            release_date = data[7] if len(data) > 7 else None  # 获取发布日期
            description = data[8] if len(data) > 8 else None  # 获取简介
            
            # 插入Source表数据
            source_sql = """
                INSERT INTO Source (
                    source_type, name, description, author, studio, 
                    release_date, status
                ) VALUES (
                    'animation', %s, %s, %s, %s, %s, 'ended'
                )
            """
            source_values = (
                title,
                description,
                author,
                studio,
                release_date
            )
            print("Source values:", source_values)  # Debug print
            
            cursor.execute(source_sql, source_values)
            source_id = cursor.lastrowid
            print("Inserted source with ID:", source_id)  # Debug print
            
            # 保存标签
            #if tags and tags != " ":
                #process_tags(tags, cursor, source_id)
            
            # 保存Bangumi网页信息
            if data[4] and len(data[4]) > 0:  # 如果有subject_id
                bangumi_url = f"https://bgm.tv{data[4][0]}"
                print("Bangumi URL:", bangumi_url)  # Debug print

                
                cursor.execute("""
                    INSERT INTO SourceWebpage (
                        website_id, source_id, url, 
                        http_status_code, crawl_time
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    WEBSITE_BANGUMI,
                    source_id,
                    bangumi_url,
                    200,  # 假设状态码为200
                    datetime.now()
                ))

                tags, links = fetch_source_tag_and_link.fetch_source_tag_and_link(bangumi_url)
                if tags:
                    for tag in tags:
                        # 插入或更新标签
                        cursor.execute("""
                            INSERT INTO SourceTag (tag, num)
                            VALUES (%s, 1)
                            ON DUPLICATE KEY UPDATE num = num + 1
                        """, (tag,))
                        
                        # 直接查询获取正确的 tag_id（避免 LAST_INSERT_ID() 的问题）
                        cursor.execute("SELECT tag_id FROM SourceTag WHERE tag = %s", (tag,))
                        tag_id = cursor.fetchone()[0]
                        
                        # 插入关系前先检查是否存在
                        cursor.execute("""
                            SELECT COUNT(*) FROM SourceTagRelation 
                            WHERE source_id = %s AND tag_id = %s
                        """, (source_id, tag_id))
                        
                        if cursor.fetchone()[0] == 0:
                            # 不存在才插入
                            cursor.execute("""
                                INSERT INTO SourceTagRelation (source_id, tag_id)
                                VALUES (%s, %s)
                            """, (source_id, tag_id))
                
                if links:
                    for link in links:
                        # 先查询该链接是否已存在
                        cursor.execute("SELECT link_id FROM ExternalLinks WHERE original_url = %s", (link,))
                        existing_record = cursor.fetchone()
                        
                        if existing_record:
                            # 链接已存在，直接获取其 ID
                            link_id = existing_record[0]
                        else:
                            # 链接不存在，插入新记录
                            cursor.execute("""
                                INSERT INTO ExternalLinks (title, original_url)
                                VALUES (%s, %s)
                            """, ('官方网站', link))
                            link_id = cursor.lastrowid  # 获取新插入记录的ID
                        
                        # 插入关系（source_id, link_id），先检查是否已存在该关系
                        cursor.execute("""
                            SELECT COUNT(*) FROM LinksOnPage 
                            WHERE source_id = %s AND link_id = %s
                        """, (source_id, link_id))
                        
                        if cursor.fetchone()[0] == 0:
                            # 关系不存在，插入新关系
                            cursor.execute("""
                                INSERT INTO LinksOnPage (source_id, link_id)
                                VALUES (%s, %s)
                            """, (source_id, link_id))
                            print(f"已建立关系: source_id={source_id}, link_id={link_id}")
                        else:
                            print(f"关系已存在: source_id={source_id}, link_id={link_id}")

                # 获取并处理角色数据
                main_characters, cover_url = add_main_character_name.getCoverAndMainCharacterName(data[4][0])
                print("Main characters:", main_characters)  # Debug print
                print("Cover URL:", cover_url)  # Debug print
                
                # 保存封面图片信息
                if cover_url:
                    cursor.execute("""
                        INSERT INTO SourceImage (
                            url, source_id
                        ) VALUES (%s, %s)
                    """, (cover_url, source_id))
                
                # 处理角色数据
                if main_characters:
                    try:
                        character_list = eval(main_characters)
                        for character in character_list:
                            print("Processing character:", character)  # Debug print
                            gender, description, birthday, voice_actor, role_image_url = get_character_info(character, bangumi_url)
                            print(gender, description, birthday, voice_actor)
                            # 插入角色基本信息
                            cursor.execute("""
                                INSERT INTO Role (name, gender, description, birthday, voice_actor)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (character, gender, description, birthday, voice_actor))
                            role_id = cursor.lastrowid
                            print("Inserted role with ID:", role_id)  # Debug print

                            cursor.execute("""
                                INSERT INTO RoleImage (image_url, format, role_id)
                                VALUES (%s, %s, %s)
                            """, (role_image_url,'jpg',role_id))
                            print(role_image_url)

                            # 插入tag
                            tags_ms = fetch_tags.fetch_tags(character)
                            # 开启事务

                            if tags_ms:
                                try:
                                    for tag in tags_ms:
                                        # 先查询标签是否存在
                                        cursor.execute("SELECT tag_id FROM RoleTag WHERE tag = %s", (tag,))
                                        result = cursor.fetchone()
                                        
                                        if result:
                                            # 标签已存在，直接获取 ID 并更新计数
                                            tag_id = result[0]
                                            cursor.execute("UPDATE RoleTag SET num = num + 1 WHERE tag_id = %s", (tag_id,))
                                        else:
                                            # 标签不存在，插入新记录
                                            cursor.execute("INSERT INTO RoleTag (tag, num) VALUES (%s, 1)", (tag,))
                                            tag_id = cursor.lastrowid  # 直接获取插入后的自增 ID
                                        
                                        # 插入关系前检查是否存在
                                        cursor.execute("""
                                            SELECT COUNT(*) FROM RoleTagRelation 
                                            WHERE role_id = %s AND tag_id = %s
                                        """, (role_id, tag_id))
                                        
                                        if cursor.fetchone()[0] == 0:
                                            cursor.execute("""
                                                INSERT INTO RoleTagRelation (role_id, tag_id)
                                                VALUES (%s, %s)
                                            """, (role_id, tag_id))
                                    
                                    # 提交事务
                                    connection.commit()
                                    
                                except Exception as e:
                                    # 发生错误时回滚
                                    connection.rollback()
                                    print(f"Error: {e}")

                            
                            # 创建角色和作品的关联
                            cursor.execute("""
                                INSERT INTO RoleSourceRelation (role_id, source_id)
                                VALUES (%s, %s)
                            """, (role_id, source_id))
                            '''
                            # 获取角色图片URL
                            image_url = fetch_image_src(character)
                            if image_url:
                                print(f"Found image for {character}: {image_url}")
                                
                                # 保存角色图片信息
                                cursor.execute("""
                                    INSERT INTO RoleImage (
                                        image_url, role_id
                                    ) VALUES (%s, %s)
                                """, (image_url, role_id))
                                
                                # 保存萌娘百科网页信息
                                moegirl_url = f"https://zh.moegirl.org.cn/{quote(character)}"
                                cursor.execute("""
                                    INSERT INTO RoleWebpage (
                                        website_id, role_id, url,
                                        http_status_code, crawl_time
                                    ) VALUES (%s, %s, %s, %s, %s)
                                """, (
                                    WEBSITE_MOEGIRL,
                                    role_id,
                                    moegirl_url,
                                    200,  # 假设状态码为200
                                    datetime.now()
                                ))
                                '''
                    except Exception as e:
                        print(f"Error processing characters for source {title}: {e}")
        
        connection.commit()
        print(f'Year {year} data saved successfully')
    except Error as e:
        print(f"Error saving data: {e}")
        connection.rollback()
    finally:
        cursor.close()

def test_getPageData():
    """测试getPageData函数返回的数据结构"""
    baseurl = 'https://bgm.tv/anime/browser/tv/airtime/2005?sort=rank&page=1'
    datalist = getPageData(baseurl)
    print("\nData structure test:")
    print("Number of items:", len(datalist))
    if datalist:
        print("\nFirst item structure:")
        for i, data in enumerate(datalist[0]):
            print(f"data[{i}]:", data)
    return datalist

def main():
    search_page_num = 1 #1页24个内容
    start_year=2020
    end_year=2023
    year_list = [i for i in range(start_year,end_year+1)]
    baseurl = 'https://bgm.tv/anime/browser/tv/airtime/{}?sort=rank&page={}'
    
    # 创建数据库连接
    connection = create_database_connection()
    if not connection:
        print("Failed to connect to database. Exiting...")
        return
    
    try:
        # 创建表
        create_tables(connection)
        
        # 爬取并保存数据
        for year in year_list:
            datalist = getYearData(year, baseurl, search_page_num)
            saveData(datalist, connection, year)
            
    except Error as e:
        print(f"Error in main: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            print("Database connection closed")

if __name__ == "__main__":  
    test_data = test_getPageData()  # 先测试数据结构
    main()
    print("爬取完毕！")

# print(get_character_info('神尾观铃', f"https://bgm.tv/subject/234"))