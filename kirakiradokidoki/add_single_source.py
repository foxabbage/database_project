# -*- codeing = utf-8 -*-
from bs4 import BeautifulSoup  # 网页解析，获取数据
import re  # 正则表达式，进行文字匹配`
from mysql.connector import Error
import kirakiradokidoki.add_main_character_name as add_main_character_name
from datetime import datetime
import kirakiradokidoki.get_anime_list_into_mydb as get_anime_list_into_mydb
import kirakiradokidoki.fetch_source_tag_and_link as fetch_source_tag_and_link




def add_single_source(urls):
    # 创建数据库连接
    connection = get_anime_list_into_mydb.create_database_connection()
    if not connection:
        print("Failed to connect to database. Exiting...")
        return
    
    if urls:
        for url in urls:
            try:
                cursor = connection.cursor()
                source_url = f"https://bgm.tv/subject/" + url
                print(source_url)
                source_html = get_anime_list_into_mydb.askURL(source_url)
                # need source_info
                # source_id INT, PK, AUTO_INCREMENT, uniquely identifies each source;
                '''
                source_type ENUM('animation', 'novel', 'manga', 'game'), DEFAULT 'animation', NOT NULL;
                name CHAR(30) NOT NULL, name of the source;
                description TEXT describe the source;
                author VARCHAR(100);                        
                studio VARCHAR(100);
                release_date DATE;
                status ENUM('not_released', 'ongoing', 'ended');
                '''
                source_soup = BeautifulSoup(source_html, "html.parser")
                #print(source_soup)
                span_tag = source_soup.find("span", class_="tip", string="中文名: ")  

                # 取 <span> 标签的下一个兄弟节点的文本（即“葬送的芙莉莲”）
                # 注意：文本可能包含空格、引号，需要清理
                name = span_tag.next_sibling.strip().strip('"') 
                print(name) # test

                cursor.execute("SELECT source_id FROM Source WHERE name = %s", (name,))
                existing_source = cursor.fetchone()

                if existing_source:
                    source_id = existing_source[0]
                    print("Source exists with ID:", source_id)  # Debug print
                    continue

                summary_div = source_soup.find('div', id='subject_summary', class_='subject_summary')
                description = summary_div.get_text(separator='\n', strip=True)
                print(description) # test


                
                # 先找到 <span> 标签
                span_tag = source_soup.find("span", class_="tip", string=re.compile(r"导演: "))  

                # 取 <span> 标签的下一个 <a> 标签的文本
                author = span_tag.find_next("a").text.strip() 
                print(author) # test

                span_tag = source_soup.find("span", class_="tip", string="动画制作: ")  

                # 取 <span> 标签的下一个 <a> 标签的文本
                studio = span_tag.find_next("a").text.strip() 
                print(studio) # test

                tip_span = source_soup.find('span', class_='tip', string='放送开始: ')
                if tip_span:
                    # 获取后面的日期文本，去除引号和可能的空白
                    date_text = tip_span.next_sibling.strip().strip('"')
                else:
                    raise ValueError("未找到‘放送开始：’对应的标签")

                # 2. 转换日期格式为 MySQL 的 DATE 类型可接受的格式（YYYY-MM-DD）
                # 将“2023年9月29日”转换为 datetime 对象
                date_obj = datetime.strptime(date_text, '%Y年%m月%d日')
                # 格式化为 MySQL DATE 类型要求的字符串形式
                release_date = date_obj.strftime('%Y-%m-%d')
                print(release_date)

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
                    name,
                    description,
                    author,
                    studio,
                    release_date
                )
                print("Source values:", source_values)  # Debug print
                
                cursor.execute(source_sql, source_values)
                source_id = cursor.lastrowid
                print("Inserted source with ID:", source_id)  # Debug print


                tags, links = fetch_source_tag_and_link.fetch_source_tag_and_link(source_url)
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
                main_characters, cover_url = add_main_character_name.getCoverAndMainCharacterName('/subject/' + url)
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
                            # Check if character already exists
                            cursor.execute("SELECT role_id FROM Role WHERE name = %s", (character,))
                            existing_role = cursor.fetchone()

                            if existing_role:
                                # Character exists, just create the relation
                                role_id = existing_role[0]
                                print("Character exists with ID:", role_id)  # Debug print

                            else:               
                                gender, description, birthday, voice_actor, role_image_url = get_anime_list_into_mydb.get_character_info(character, source_url)
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
                                tags_ms = get_anime_list_into_mydb.fetch_tags.fetch_tags(character)
                                # 开启事务

                                if tags_ms:
                                    print(tags_ms)
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
                                    
                                    except Exception as e:
                                        # 发生错误时回滚
                                        connection.rollback()
                                        print(f"Error: {e}")

                            # 创建角色和作品的关联
                            cursor.execute("""
                                INSERT INTO RoleSourceRelation (role_id, source_id)
                                VALUES (%s, %s)
                            """, (role_id, source_id))  

                            

                    except Exception as e:
                        print(f"Error processing characters for source {name}: {e}")



                connection.commit()
            except Error as e:
                print(f"Error saving data: {e}")
                connection.rollback()
            finally:
                cursor.close()