from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from typing import Any, Optional
from sqlalchemy.engine import Result

# 模拟数据库接口
class DatabaseAPI:
    _engine = None
    _Session = None

    @classmethod
    def initialize(cls, connection_string):
        """初始化数据库连接"""
        cls._engine = create_engine(connection_string)
        cls._Session = sessionmaker(bind=cls._engine)

    @classmethod
    def get_session(cls):
        """获取数据库会话"""
        if not cls._Session:
            raise Exception("Database not initialized. Call initialize() first.")
        return cls._Session()

    @staticmethod
    def search_images_by_name(name, imgtype=1, page=1, per_page=100):
        """用角色/作品名搜图片
        参数：
        - name: 角色/作品名
        - imgtype: 1表示角色图片，2表示作品图片
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(f"搜索图片: name={name}, imgtype={imgtype}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page
            
            if imgtype == 1:  # 角色图片
                query = text("""
                    SELECT ri.role_id, ri.image_url, r.name, r.description, ri.is_downloaded, ri.local_path
                    FROM RoleImage ri
                    JOIN Role r ON ri.role_id = r.role_id
                    WHERE r.name LIKE :name
                    LIMIT :limit OFFSET :offset
                """)
                images = session.execute(query, {
                    "name": f"%{name}%",
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text("""
                    SELECT COUNT(*) 
                    FROM RoleImage ri
                    JOIN Role r ON ri.role_id = r.role_id
                    WHERE r.name LIKE :name
                """)
                total = session.execute(count_query, {"name": f"%{name}%"}).scalar()
                
                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'is_downloaded': img[4],
                        'local_path': img[5]
                    })
                
            else:  # 作品图片
                query = text("""
                    SELECT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path
                    FROM SourceImage si
                    JOIN Source s ON si.source_id = s.source_id
                    WHERE s.name LIKE :name
                    LIMIT :limit OFFSET :offset
                """)
                images = session.execute(query, {
                    "name": f"%{name}%",
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text("""
                    SELECT COUNT(*) 
                    FROM SourceImage si
                    JOIN Source s ON si.source_id = s.source_id
                    WHERE s.name LIKE :name
                """)
                total = session.execute(count_query, {"name": f"%{name}%"}).scalar()
                
                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'source_type': img[4],
                        'is_downloaded': img[5],
                        'local_path': img[6]
                    })
            
            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()
    
    @staticmethod
    def fetch_all_images(imgtype=1, page=1, per_page=100):
        """获取所有图片
        参数：
        - imgtype: 1表示角色图片，2表示作品图片
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(f"获取所有图片: imgtype={imgtype}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page
            
            if imgtype == 1:  # 角色图片
                query = text("""
                    SELECT ri.role_id, ri.image_url, r.name, r.description, ri.is_downloaded, ri.local_path
                    FROM RoleImage ri
                    JOIN Role r ON ri.role_id = r.role_id
                    LIMIT :limit OFFSET :offset
                """)
                images = session.execute(query, {
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text("SELECT COUNT(*) FROM RoleImage")
                total = session.execute(count_query).scalar()
                
                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'is_downloaded': img[4],
                        'local_path': img[5]
                    })
            
            else:  # 作品图片
                query = text("""
                    SELECT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path
                    FROM SourceImage si
                    JOIN Source s ON si.source_id = s.source_id
                    LIMIT :limit OFFSET :offset
                """)
                images = session.execute(query, {
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text("SELECT COUNT(*) FROM SourceImage")
                total = session.execute(count_query).scalar()

                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'source_type': img[4],
                        'is_downloaded': img[5],
                        'local_path': img[6]
                    })
            
            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()
    
    @staticmethod
    def search_images_by_tags(tagli, imgtype=1, page=1, per_page=100):
        """用标签搜索图片
        参数：
        - tagli: 标签列表
        - imgtype: 1表示角色图片，2表示作品图片
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(f"根据标签搜索图片: tagli={tagli}, imgtype={imgtype}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page
            
            if imgtype == 1:  # 角色图片
                # 构建标签条件
                tag_conditions = " OR ".join([f"t.tag = :tag{i}" for i in range(len(tagli))])
                tag_params = {f"tag{i}": tag for i, tag in enumerate(tagli)}
                
                query = text(f"""
                    SELECT DISTINCT ri.role_id, ri.image_url, r.name, r.description, ri.is_downloaded, ri.local_path
                    FROM RoleImage ri
                    JOIN Role r ON ri.role_id = r.role_id
                    JOIN RoleTagRelation rtr ON r.role_id = rtr.role_id
                    JOIN RoleTag t ON rtr.tag_id = t.tag_id
                    WHERE {tag_conditions}
                    LIMIT :limit OFFSET :offset
                """)
                
                images = session.execute(query, {
                    **tag_params,
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text(f"""
                    SELECT COUNT(DISTINCT ri.role_id)
                    FROM RoleImage ri
                    JOIN Role r ON ri.role_id = r.role_id
                    JOIN RoleTagRelation rtr ON r.role_id = rtr.role_id
                    JOIN RoleTag t ON rtr.tag_id = t.tag_id
                    WHERE {tag_conditions}
                """)
                total = session.execute(count_query, tag_params).scalar()

                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'is_downloaded': img[4],
                        'local_path': img[5]
                    })
                
            else:  # 作品图片
                # 构建标签条件
                tag_conditions = " OR ".join([f"t.tag = :tag{i}" for i in range(len(tagli))])
                tag_params = {f"tag{i}": tag for i, tag in enumerate(tagli)}
                
                query = text(f"""
                    SELECT DISTINCT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path
                    FROM SourceImage si
                    JOIN Source s ON si.source_id = s.source_id
                    JOIN SourceTagRelation str ON s.source_id = str.source_id
                    JOIN SourceTag t ON str.tag_id = t.tag_id
                    WHERE {tag_conditions}
                    LIMIT :limit OFFSET :offset
                """)
                
                images = session.execute(query, {
                    **tag_params,
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text(f"""
                    SELECT COUNT(DISTINCT si.source_id)
                    FROM SourceImage si
                    JOIN Source s ON si.source_id = s.source_id
                    JOIN SourceTagRelation str ON s.source_id = str.source_id
                    JOIN SourceTag t ON str.tag_id = t.tag_id
                    WHERE {tag_conditions}
                """)
                total = session.execute(count_query, tag_params).scalar()

                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'source_type': img[4],
                        'is_downloaded': img[5],
                    })
            
            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()
    
    @staticmethod
    def search_images_by_name_and_tags(name, tagli, imgtype=1, page=1, per_page=100):
        """根据名称和标签搜索图片
        参数：
        - name: 名称
        - tagli: 标签列表
        - imgtype: 1表示角色图片，2表示作品图片
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(f"根据名称和标签搜索图片: name={name}, tagli={tagli}, imgtype={imgtype}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page
            
            if imgtype == 1:  # 角色图片
                # 构建标签条件
                tag_conditions = " OR ".join([f"t.tag = :tag{i}" for i in range(len(tagli))])
                tag_params = {f"tag{i}": tag for i, tag in enumerate(tagli)}
                
                query = text(f"""
                    SELECT DISTINCT ri.role_id, ri.image_url, r.name, r.description, ri.is_downloaded, ri.local_path
                    FROM RoleImage ri
                    JOIN Role r ON ri.role_id = r.role_id
                    JOIN RoleTagRelation rtr ON r.role_id = rtr.role_id
                    JOIN RoleTag t ON rtr.tag_id = t.tag_id
                    WHERE r.name LIKE :name AND ({tag_conditions})
                    LIMIT :limit OFFSET :offset
                """)
                
                images = session.execute(query, {
                    "name": f"%{name}%",
                    **tag_params,
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text(f"""
                    SELECT COUNT(DISTINCT ri.role_id)
                    FROM RoleImage ri
                    JOIN Role r ON ri.role_id = r.role_id
                    JOIN RoleTagRelation rtr ON r.role_id = rtr.role_id
                    JOIN RoleTag t ON rtr.tag_id = t.tag_id
                    WHERE r.name LIKE :name AND ({tag_conditions})
                """)
                total = session.execute(count_query, {
                    "name": f"%{name}%",
                    **tag_params
                }).scalar()
                
                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'is_downloaded': img[4],
                        'local_path': img[5]
                    })
            
            else:  # 作品图片
                # 构建标签条件
                tag_conditions = " OR ".join([f"t.tag = :tag{i}" for i in range(len(tagli))])
                tag_params = {f"tag{i}": tag for i, tag in enumerate(tagli)}
                
                query = text(f"""
                    SELECT DISTINCT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path
                    FROM SourceImage si
                    JOIN Source s ON si.source_id = s.source_id
                    JOIN SourceTagRelation str ON s.source_id = str.source_id
                    JOIN SourceTag t ON str.tag_id = t.tag_id
                    WHERE s.name LIKE :name AND ({tag_conditions})
                    LIMIT :limit OFFSET :offset
                """)
                
                images = session.execute(query, {
                    "name": f"%{name}%",
                    **tag_params,
                    "limit": per_page,
                    "offset": offset
                }).fetchall()
                
                count_query = text(f"""
                    SELECT COUNT(DISTINCT si.source_id)
                    FROM SourceImage si
                    JOIN Source s ON si.source_id = s.source_id
                    JOIN SourceTagRelation str ON s.source_id = str.source_id
                    JOIN SourceTag t ON str.tag_id = t.tag_id
                    WHERE s.name LIKE :name AND ({tag_conditions})
                """)
                total = session.execute(count_query, {
                    "name": f"%{name}%",
                    **tag_params
                }).scalar()
                
                image_list = []
                for img in images:
                    image_list.append({
                        'id': img[0],
                        'url': img[1],
                        'name': img[2],
                        'description': img[3],
                        'source_type': img[4],
                        'is_downloaded': img[5],
                        'local_path': img[6]
                    })
            
            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()
    
    @staticmethod
    def get_image_details_role(role_id):
        """获取角色图片详情
        参数：
        - role_id: 角色ID
        返回：角色详细信息
        """
        print(f"获取角色详情: role_id={role_id}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                SELECT r.role_id, r.name, r.gender, r.birthday, r.voice_actor, r.description
                FROM Role r
                WHERE r.role_id = :role_id
            """)
            result = session.execute(query, {"role_id": role_id}).fetchone()
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'name': result[1],
                'gender': result[2],
                'birthday': result[3],
                'voice_actor': result[4],
                'description': result[5]
            }
        finally:
            session.close()
    
    @staticmethod
    def get_image_list_role(role_id):
        """角色id搜角色图片
        参数：
        - role_id: 角色ID
        返回：图片列表
        """
        print(f"获取角色图片详情: role_id={role_id}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                SELECT ri.image_url, ri.is_downloaded, ri.local_path
                FROM Role r
                JOIN RoleImage ri ON r.role_id = ri.role_id
                WHERE r.role_id = :role_id
            """)
            images = session.execute(query, {"role_id": role_id}).fetchall()
            
            image_list = []
            for img in images:
                image_list.append({
                    'url': img[0],
                    'is_downloaded': img[1],
                    'local_path': img[2]
                })
            
            return image_list
        finally:
            session.close()
    
    @staticmethod
    def get_image_details_source(source_id):
        """获取作品详情
        参数：
        - source_id: 作品ID
        返回：作品详细信息
        """
        print(f"获取作品图片详情: source_id={source_id}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                SELECT s.source_id, s.name, s.source_type, s.author, s.studio, s.release_date, s.status, s.description
                FROM Source s
                WHERE s.source_id = :source_id
            """)
            result = session.execute(query, {"source_id": source_id}).fetchone()
            
            if not result:
                return None
            
            return {
                'id': result[0],
                'name': result[1],
                'source_type': result[2],
                'author': result[3],
                'studio': result[4],
                'release_date': result[5],
                'status': result[6],
                'description': result[7]
            }
        finally:
            session.close()
    
    @staticmethod
    def get_image_list_source(source_id):
        """获取作品的所有图片
        参数：
        - source_id: 作品ID
        返回：图片列表
        """
        print(f"获取作品的所有图片: source_id={source_id}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                SELECT si.url, si.is_downloaded, si.local_path
                FROM Source s
                JOIN SourceImage si ON s.source_id = si.source_id
                WHERE s.source_id = :source_id
            """)
            images = session.execute(query, {"source_id": source_id}).fetchall()
            
            image_list = []
            for img in images:
                image_list.append({
                    'url': img[0],
                    'is_downloaded': img[1],
                    'local_path': img[2]
                })
            
            return image_list
        finally:
            session.close()
    
    @staticmethod
    def get_tags_list(tagtype:int):
        """获取标签列表
        参数：
        - tagtype: 1表示角色标签，2表示来源标签
        返回：标签列表
        """
        print(f"获取标签列表: tagtype={tagtype}")
        session = DatabaseAPI.get_session()
        try:
            if tagtype == 1:
                query = text("SELECT tag FROM RoleTag")
            else:
                query = text("SELECT tag FROM SourceTag")
            
            tags = session.execute(query).fetchall()
            return [tag[0] for tag in tags]
        finally:
            session.close()
    
    @staticmethod
    def get_tags_list_by_id(tagtype, id):
        """获取某个角色或者作品的标签列表
        参数：
        - tagtype: 1表示角色标签，2表示来源标签
        - id: 角色或者作品的ID
        返回：标签列表
        """
        print(f"获取图片的标签列表: tagtype={tagtype}, id={id}")
        session = DatabaseAPI.get_session()
        try:
            if tagtype == 1:
                query = text("""
                    SELECT t.tag
                    FROM RoleTag t
                    JOIN RoleTagRelation rtr ON t.tag_id = rtr.tag_id
                    WHERE rtr.role_id = :id
                """)
            else:
                query = text("""
                    SELECT t.tag
                    FROM SourceTag t
                    JOIN SourceTagRelation str ON t.tag_id = str.tag_id
                    WHERE str.source_id = :id
                """)
            
            tags = session.execute(query, {"id": id}).fetchall()
            return [tag[0] for tag in tags]
        finally:
            session.close()
    
    @staticmethod
    def get_external_link_list(source_id):
        """获取外部链接列表
        参数：
        - source_id: 作品ID
        返回：外部链接列表
        """
        print(f"获取外部链接列表: source_id={source_id}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                SELECT el.title, el.original_url
                FROM ExternalLinks el
                JOIN LinksOnPage lop ON el.link_id = lop.link_id
                WHERE lop.source_id = :source_id
            """)
            links = session.execute(query, {"source_id": source_id}).fetchall()
            
            link_list = []
            for link in links:
                link_list.append({
                    'title': link[0],
                    'original_url': link[1]
                })
            
            return link_list
        finally:
            session.close()
    
    @staticmethod
    def get_source_of_role(role_id):
        """获取角色的来源作品
        参数：
        - role_id: 角色ID
        返回：作品列表
        """
        print(f"获取角色的来源作品: role_id={role_id}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                SELECT s.source_id, s.name
                FROM Source s
                JOIN RoleSourceRelation rsr ON s.source_id = rsr.source_id
                JOIN Role r ON r.role_id = rsr.role_id
                WHERE r.role_id = :role_id
            """)
            sources = session.execute(query, {"role_id": role_id}).fetchall()
            
            source_list = []
            for source in sources:
                source_list.append({
                    'source_id': source[0],
                    'name': source[1]
                })
            
            return source_list
        finally:
            session.close()
    
    @staticmethod
    def get_role_list(source_id):
        """获取作品中的角色
        参数：
        - source_id: 作品ID
        返回：角色列表
        """
        print(f"获取作品中的角色: source_id={source_id}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                SELECT r.role_id, r.name
                FROM Role r
                JOIN RoleSourceRelation rsr ON r.role_id = rsr.role_id
                WHERE rsr.source_id = :source_id
            """)
            roles = session.execute(query, {"source_id": source_id}).fetchall()
            
            role_list = []
            for role in roles:
                role_list.append({
                    'role_id': role[0],
                    'name': role[1]
                })
            
            return role_list
        finally:
            session.close()

    @staticmethod
    def save_details_to_database(details, imgtype):
        """保存数据详情到数据库
        参数：
        - details: 包含详情的字典
        - imgtype: 1表示角色图片，2表示作品图片
        返回：更新的行数
        """
        print(f"保存数据详情到数据库: imgtype={imgtype}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:  # 角色
                query = text("""
                    UPDATE Role r
                    SET r.name = :name,
                        r.gender = :gender,
                        r.birthday = :birthday,
                        r.voice_actor = :voice_actor,
                        r.description = :description
                    WHERE r.role_id = :id
                """)
            else:  # 作品
                query = text("""
                    UPDATE Source s
                    SET s.name = :name,
                        s.source_type = :source_type,
                        s.author = :author,
                        s.studio = :studio,
                        s.release_date = :release_date,
                        s.status = :status,
                        s.description = :description
                    WHERE s.source_id = :id
                """)
            
            result = session.execute(query, details)
            session.commit()
            return result.rowcount
        except Exception as e:
            session.rollback()
            print(f"保存详情失败: {str(e)}")
            return 0
        finally:
            session.close()

    @staticmethod
    def delete_tags_by_id(tags, id, imgtype):
        """删除标签
        参数：
        - tags: 要删除的标签列表
        - id: 角色或作品ID
        - imgtype: 1表示角色图片，2表示作品图片
        返回：删除的标签数量
        """
        print(f"删除标签: tags={tags}, id={id}, imgtype={imgtype}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:  # 角色
                delete_query = text("""
                    DELETE rtr FROM RoleTagRelation rtr
                    JOIN RoleTag t ON rtr.tag_id = t.tag_id
                    WHERE rtr.role_id = :role_id AND t.tag IN :tags
                """)
                result = session.execute(delete_query, {
                    "role_id": id,
                    "tags": tuple(tags)
                })
                
                # 更新标签数量
                update_query = text("""
                    UPDATE RoleTag t
                    SET t.num = (
                        SELECT COUNT(*) 
                        FROM RoleTagRelation rtr 
                        WHERE rtr.tag_id = t.tag_id
                    )
                    WHERE t.tag IN :tags
                """)
                session.execute(update_query, {"tags": tuple(tags)})
                
            else:  # 作品
                delete_query = text("""
                    DELETE str FROM SourceTagRelation str
                    JOIN SourceTag t ON str.tag_id = t.tag_id
                    WHERE str.source_id = :source_id AND t.tag IN :tags
                """)
                result = session.execute(delete_query, {
                    "source_id": id,
                    "tags": tuple(tags)
                })
                
                # 更新标签数量
                update_query = text("""
                    UPDATE SourceTag t
                    SET t.num = (
                        SELECT COUNT(*) 
                        FROM SourceTagRelation str 
                        WHERE str.tag_id = t.tag_id
                    )
                    WHERE t.tag IN :tags
                """)
                session.execute(update_query, {"tags": tuple(tags)})
            
            session.commit()
            return result.rowcount
        except Exception as e:
            session.rollback()
            print(f"删除标签失败: {str(e)}")
            return 0
        finally:
            session.close()

    @staticmethod
    def add_tags_by_id(tags, id, imgtype):
        """添加标签
        参数：
        - tags: 要添加的标签列表
        - id: 角色或作品ID
        - imgtype: 1表示角色图片，2表示作品图片
        返回：添加的标签数量
        """
        print(f"添加图片标签: tags={tags}, id={id}, imgtype={imgtype}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:  # 角色图片
                insert_query = text("""
                    INSERT IGNORE INTO RoleTagRelation (role_id, tag_id)
                    SELECT :role_id, t.tag_id
                    FROM RoleTag t
                    WHERE t.tag IN :tags
                """)
                result = session.execute(insert_query, {
                    "role_id": id,
                    "tags": tuple(tags)
                })
                
                # 更新标签数量
                update_query = text("""
                    UPDATE RoleTag t
                    SET t.num = (
                        SELECT COUNT(*) 
                        FROM RoleTagRelation rtr 
                        WHERE rtr.tag_id = t.tag_id
                    )
                    WHERE t.tag IN :tags
                """)
                session.execute(update_query, {"tags": tuple(tags)})
                
            else:  # 作品图片
                insert_query = text("""
                    INSERT IGNORE INTO SourceTagRelation (source_id, tag_id)
                    SELECT :source_id, t.tag_id
                    FROM SourceTag t
                    WHERE t.tag IN :tags
                """)
                result = session.execute(insert_query, {
                    "source_id": id,
                    "tags": tuple(tags)
                })
                
                # 更新标签数量
                update_query = text("""
                    UPDATE SourceTag t
                    SET t.num = (
                        SELECT COUNT(*) 
                        FROM SourceTagRelation str 
                        WHERE str.tag_id = t.tag_id
                    )
                    WHERE t.tag IN :tags
                """)
                session.execute(update_query, {"tags": tuple(tags)})
            
            session.commit()
            return result.rowcount
        except Exception as e:
            session.rollback()
            print(f"添加标签失败: {str(e)}")
            return 0
        finally:
            session.close()

    @staticmethod
    def delete_by_id(id, imgtype):
        """删除角色或作品及其关联数据
        参数：
        - id: 角色或作品ID
        - imgtype: 1表示角色，2表示作品
        返回：删除的角色或作品ID列表
        """
        print(f"删除条目: id={id}, imgtype={imgtype}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:  # 角色
                # 获取关联的角色ID列表（包括自身）
                role_query = text("""
                    SELECT role_id 
                    FROM Role 
                    WHERE role_id = :role_id
                """)
                role_ids = [row[0] for row in session.execute(role_query, {"role_id": id}).fetchall()]
                
                if not role_ids:
                    return []
                
                # 获取该角色关联的所有标签ID，用于后续更新标签数量
                tag_query = text("""
                    SELECT DISTINCT t.tag_id
                    FROM RoleTag t
                    JOIN RoleTagRelation rtr ON t.tag_id = rtr.tag_id
                    WHERE rtr.role_id = :role_id
                """)
                tag_ids = [row[0] for row in session.execute(tag_query, {"role_id": id}).fetchall()]
                
                # 删除角色及其关联数据
                delete_role = text("DELETE FROM Role WHERE role_id = :role_id")
                session.execute(delete_role, {"role_id": id})
                
                # 更新相关标签的数量
                if tag_ids:
                    update_tag_query = text("""
                        UPDATE RoleTag t
                        SET t.num = (
                            SELECT COUNT(*) 
                            FROM RoleTagRelation rtr 
                            WHERE rtr.tag_id = t.tag_id
                        )
                        WHERE t.tag_id IN :tag_ids
                    """)
                    session.execute(update_tag_query, {"tag_ids": tuple(tag_ids)})
                
                session.commit()
                return role_ids
                
            else:  # 作品
                # 获取关联的角色ID列表
                role_query = text("""
                    SELECT r.role_id 
                    FROM Role r
                    JOIN RoleSourceRelation rsr ON r.role_id = rsr.role_id
                    WHERE rsr.source_id = :source_id
                """)
                role_ids = [row[0] for row in session.execute(role_query, {"source_id": id}).fetchall()]
                
                # 获取该作品关联的所有标签ID，用于后续更新标签数量
                tag_query = text("""
                    SELECT DISTINCT t.tag_id
                    FROM SourceTag t
                    JOIN SourceTagRelation str ON t.tag_id = str.tag_id
                    WHERE str.source_id = :source_id
                """)
                tag_ids = [row[0] for row in session.execute(tag_query, {"source_id": id}).fetchall()]
                
                # 删除作品及其关联数据
                delete_source = text("DELETE FROM Source WHERE source_id = :source_id")
                session.execute(delete_source, {"source_id": id})
                
                # 更新相关标签的数量
                if tag_ids:
                    update_tag_query = text("""
                        UPDATE SourceTag t
                        SET t.num = (
                            SELECT COUNT(*) 
                            FROM SourceTagRelation str 
                            WHERE str.tag_id = t.tag_id
                        )
                        WHERE t.tag_id IN :tag_ids
                    """)
                    session.execute(update_tag_query, {"tag_ids": tuple(tag_ids)})
                
                session.commit()
                return role_ids
                
        except Exception as e:
            session.rollback()
            print(f"删除失败: {str(e)}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_all_tags_and_num(imgtype, page, per_page):
        """获取所有标签及其数量
        参数：
        - imgtype: 1表示角色标签，2表示来源标签
        - page: 页码
        - per_page: 每页数量
        返回：标签列表和总数
        """
        print(f"获取所有标签: imgtype={imgtype}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page
            
            if imgtype == 1:
                # 获取角色标签
                query = text("""
                    SELECT tag, num
                    FROM RoleTag
                    ORDER BY num DESC
                    LIMIT :limit OFFSET :offset
                """)
                count_query = text("SELECT COUNT(*) FROM RoleTag")
            else:
                # 获取来源标签
                query = text("""
                    SELECT tag, num
                    FROM SourceTag
                    ORDER BY num DESC
                    LIMIT :limit OFFSET :offset
                """)
                count_query = text("SELECT COUNT(*) FROM SourceTag")
            
            tags = session.execute(query, {
                "limit": per_page,
                "offset": offset
            }).fetchall()
            
            total = session.execute(count_query).scalar()
            
            return {
                'total': total,
                'tags_and_nums': [{'tag': tag[0], 'num': tag[1]} for tag in tags]
            }
        finally:
            session.close()

    @staticmethod
    def get_all_tags_and_num_by_name(imgtype, tagname, page, per_page):
        """根据名称搜索标签及其数量
        参数：
        - imgtype: 1表示角色标签，2表示来源标签
        - tagname: 标签名称
        - page: 页码
        - per_page: 每页数量
        返回：标签列表和总数
        """
        print(f"搜索标签: imgtype={imgtype}, tagname={tagname}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page
            
            if imgtype == 1:
                # 搜索角色标签
                query = text("""
                    SELECT tag, num
                    FROM RoleTag
                    WHERE tag LIKE :tagname
                    ORDER BY num DESC
                    LIMIT :limit OFFSET :offset
                """)
                count_query = text("""
                    SELECT COUNT(*)
                    FROM RoleTag
                    WHERE tag LIKE :tagname
                """)
            else:
                # 搜索来源标签
                query = text("""
                    SELECT tag, num
                    FROM SourceTag
                    WHERE tag LIKE :tagname
                    ORDER BY num DESC
                    LIMIT :limit OFFSET :offset
                """)
                count_query = text("""
                    SELECT COUNT(*)
                    FROM SourceTag
                    WHERE tag LIKE :tagname
                """)
            
            tags = session.execute(query, {
                "tagname": f"%{tagname}%",
                "limit": per_page,
                "offset": offset
            }).fetchall()
            
            total = session.execute(count_query, {"tagname": f"%{tagname}%"}).scalar()
            
            return {
                'total': total,
                'tags_and_nums': [{'tag': tag[0], 'num': tag[1]} for tag in tags]
            }
        finally:
            session.close()

    @staticmethod
    def check_tag_exist(imgtype, tagname):
        """检查标签是否存在
        参数：
        - imgtype: 1表示角色标签，2表示来源标签
        - tagname: 需要检查的标签名称
        返回：若存在则返回True否则False
        """
        print(f"检查标签是否存在: imgtype={imgtype}, tagname={tagname}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:
                query = text("SELECT 1 FROM RoleTag WHERE tag = :tag")
            else:
                query = text("SELECT 1 FROM SourceTag WHERE tag = :tag")
            
            result = session.execute(query, {"tag": tagname}).fetchone()
            return result is not None
        finally:
            session.close()

    @staticmethod
    def add_tag(imgtype, tagname):
        """添加标签
        参数：
        - imgtype: 1表示角色标签，2表示来源标签
        - tagname: 需要添加的标签名
        返回：添加成功返回True
        """
        print(f"添加标签: imgtype={imgtype}, tagname={tagname}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:
                query = text("""
                    INSERT INTO RoleTag (tag, num)
                    VALUES (:tag, 0)
                """)
            else:
                query = text("""
                    INSERT INTO SourceTag (tag, num)
                    VALUES (:tag, 0)
                """)
            
            try:
                session.execute(query, {"tag": tagname})
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"添加标签失败: {str(e)}")
                return False
        finally:
            session.close()

    @staticmethod
    def delete_tag(imgtype, tagname):
        """删除标签
        参数：
        - imgtype: 1表示角色标签，2表示来源标签
        - tagname: 需要删除的标签名
        返回：删除成功返回True
        """
        print(f"删除标签: imgtype={imgtype}, tagname={tagname}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:
                # 首先删除所有关联关系
                delete_relations = text("""
                    DELETE rtr FROM RoleTagRelation rtr
                    JOIN RoleTag t ON rtr.tag_id = t.tag_id
                    WHERE t.tag = :tag
                """)
                session.execute(delete_relations, {"tag": tagname})
                
                # 然后删除标签
                delete_tag = text("DELETE FROM RoleTag WHERE tag = :tag")
                result = session.execute(delete_tag, {"tag": tagname})
                
            else:
                # 首先删除所有关联关系
                delete_relations = text("""
                    DELETE str FROM SourceTagRelation str
                    JOIN SourceTag t ON str.tag_id = t.tag_id
                    WHERE t.tag = :tag
                """)
                session.execute(delete_relations, {"tag": tagname})
                
                # 然后删除标签
                delete_tag = text("DELETE FROM SourceTag WHERE tag = :tag")
                result = session.execute(delete_tag, {"tag": tagname})
            
            session.commit()
            return result.rowcount > 0
        except Exception as e:
            session.rollback()
            print(f"删除标签失败: {str(e)}")
            return False
        finally:
            session.close()

    @staticmethod
    def test_exist_by_id(id, imgtype):
        """检查是否存在
        参数：
        - imgtype: 1表示角色，2表示作品
        - id: 需要检查的角色或作品ID
        返回：存在返回True
        """
        print(f"检查ID是否存在: id={id}, imgtype={imgtype}")
        session = DatabaseAPI.get_session()
        try:
            if imgtype == 1:
                query = text("SELECT 1 FROM Role WHERE role_id = :id")
            else:
                query = text("SELECT 1 FROM Source WHERE source_id = :id")
            
            result = session.execute(query, {"id": id}).fetchone()
            return result is not None
        finally:
            session.close()

    @staticmethod
    def add_spider(name, bangumi_idlist, download_to_local):
        """添加爬虫数据
        参数：
        - name: 爬虫名称
        - bangumi_idlist: bangumi ID列表（字符串格式）
        - download_to_local: 是否下载到本地
        返回：添加成功返回True
        """
        print(f"添加爬虫: name={name}, bangumi_idlist={bangumi_idlist}, download_to_local={download_to_local}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                INSERT INTO Spider (name, request_id_para, download_to_local, status)
                VALUES (:name, :request_id_para, :download_to_local, 'active')
            """)
            
            try:
                session.execute(query, {
                    "name": name,
                    "request_id_para": bangumi_idlist,
                    "download_to_local": download_to_local
                })
                session.commit()
                print("添加爬虫成功")
                return True
            except Exception as e:
                session.rollback()
                print(f"添加爬虫失败: {str(e)}")
                return False
        finally:
            session.close()

    @staticmethod
    def get_all_spiders_and_status(page, per_page):
        """获取爬虫列表
        参数：
        - page: 页码
        - per_page: 每页数量
        返回：{
            'total': 总爬虫数,
            'spiders_and_status': [
                {'name': 爬虫名称, 'status': 状态},
                ...
            ]
        }
        """
        print(f"获取爬虫列表: page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page
            
            # 获取爬虫列表
            query = text("""
                SELECT name, status
                FROM Spider
                ORDER BY name
                LIMIT :limit OFFSET :offset
            """)
            spiders = session.execute(query, {
                "limit": per_page,
                "offset": offset
            }).fetchall()
            
            # 获取总数
            count_query = text("SELECT COUNT(*) FROM Spider")
            total = session.execute(count_query).scalar()
            
            return {
                'total': total,
                'spiders_and_status': [{'name': spider[0], 'status': spider[1]} for spider in spiders]
            }
        finally:
            session.close()

    @staticmethod
    def expire_spider(name):
        """删除爬虫
        参数：
        - name: 爬虫名称
        返回：更新成功返回True
        """
        print(f"删除爬虫: name={name}")
        session = DatabaseAPI.get_session()
        try:
            # 首先检查是否存在符合条件的爬虫
            check_query = text("""
                SELECT 1 FROM Spider
                WHERE name = :name AND status IN ('active', 'inactive')
            """)
            exists = session.execute(check_query, {"name": name}).fetchone() is not None
            
            if not exists:
                return False
                
            # 更新爬虫状态
            update_query = text("""
                UPDATE Spider
                SET status = 'expired'
                WHERE name = :name AND status IN ('active', 'inactive')
            """)
            
            try:
                session.execute(update_query, {"name": name})
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"删除爬虫失败: {str(e)}")
                return False
        finally:
            session.close()

    @staticmethod
    def resume_spider(name):
        """激活爬虫
        参数：
        - name: 爬虫名称
        返回：更新成功返回True
        """
        print(f"激活爬虫: name={name}")
        session = DatabaseAPI.get_session()
        try:
            # 首先检查是否存在符合条件的爬虫
            check_query = text("""
                SELECT 1 FROM Spider
                WHERE name = :name AND status IN ('inactive')
            """)
            exists = session.execute(check_query, {"name": name}).fetchone() is not None

            if not exists:
                return False

            # 更新爬虫状态
            update_query = text("""
                UPDATE Spider
                SET status = 'active'
                WHERE name = :name AND status IN ('inactive')
            """)

            try:
                session.execute(update_query, {"name": name})
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"激活爬虫失败: {str(e)}")
                return False
        finally:
            session.close()

    @staticmethod
    def pause_spider(name):
        """暂停爬虫
        参数：
        - name: 爬虫名称
        返回：更新成功返回True
        """
        print(f"暂停爬虫: name={name}")
        session = DatabaseAPI.get_session()
        try:
            # 首先检查是否存在符合条件的爬虫
            check_query = text("""
                SELECT 1 FROM Spider
                WHERE name = :name AND status IN ('active')
            """)
            exists = session.execute(check_query, {"name": name}).fetchone() is not None

            if not exists:
                return False

            # 更新爬虫状态
            update_query = text("""
                UPDATE Spider
                SET status = 'inactive'
                WHERE name = :name AND status IN ('active')
            """)

            try:
                session.execute(update_query, {"name": name})
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"暂停爬虫失败: {str(e)}")
                return False
        finally:
            session.close()

    @staticmethod
    def search_images_by_name_order_by_time(name, page=1, per_page=100):
        """用角色/作品名搜图片
        参数：
        - name: 角色/作品名
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(f"搜索图片: name={name}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page

            query = text("""
                SELECT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path, s.release_date
                FROM SourceImage si
                JOIN Source s ON si.source_id = s.source_id
                WHERE s.name LIKE :name
                ORDER BY s.release_date DESC
                LIMIT :limit OFFSET :offset
                """)
            images = session.execute(query, {
                "name": f"%{name}%",
                "limit": per_page,
                "offset": offset
            }).fetchall()

            count_query = text("""
                SELECT COUNT(*) 
                FROM SourceImage si
                JOIN Source s ON si.source_id = s.source_id
                WHERE s.name LIKE :name
            """)
            total = session.execute(count_query, {"name": f"%{name}%"}).scalar()

            image_list = []
            for img in images:
                image_list.append({
                    'id': img[0],
                    'url': img[1],
                    'name': img[2],
                    'description': img[3],
                    'source_type': img[4],
                    'is_downloaded': img[5],
                    'local_path': img[6]
                })

            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()

    @staticmethod
    def fetch_all_images_order_by_time(page=1, per_page=100):
        """获取所有图片
        参数：
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(f"获取所有图片: page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page

            query = text("""
                SELECT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path, s.release_date
                FROM SourceImage si
                JOIN Source s ON si.source_id = s.source_id
                ORDER BY s.release_date DESC
                LIMIT :limit OFFSET :offset
            """)
            images = session.execute(query, {
                "limit": per_page,
                "offset": offset
            }).fetchall()

            count_query = text("SELECT COUNT(*) FROM SourceImage")
            total = session.execute(count_query).scalar()

            image_list = []
            for img in images:
                image_list.append({
                    'id': img[0],
                    'url': img[1],
                    'name': img[2],
                    'description': img[3],
                    'source_type': img[4],
                    'is_downloaded': img[5],
                    'local_path': img[6]
                })

            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()

    @staticmethod
    def search_images_by_tags_order_by_time(tagli, page=1, per_page=100):
        """用标签搜索图片
        参数：
        - tagli: 标签列表
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(f"根据标签搜索图片: tagli={tagli}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page

            # 构建标签条件
            tag_conditions = " OR ".join([f"t.tag = :tag{i}" for i in range(len(tagli))])
            tag_params = {f"tag{i}": tag for i, tag in enumerate(tagli)}

            query = text(f"""
                SELECT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path, s.release_date
                FROM SourceImage si
                JOIN Source s ON si.source_id = s.source_id
                JOIN SourceTagRelation str ON s.source_id = str.source_id
                JOIN SourceTag t ON str.tag_id = t.tag_id
                WHERE {tag_conditions}
                ORDER BY s.release_date DESC
                LIMIT :limit OFFSET :offset
            """)

            images = session.execute(query, {
                **tag_params,
                "limit": per_page,
                "offset": offset
            }).fetchall()

            count_query = text(f"""
                SELECT COUNT(DISTINCT si.source_id)
                FROM SourceImage si
                JOIN Source s ON si.source_id = s.source_id
                JOIN SourceTagRelation str ON s.source_id = str.source_id
                JOIN SourceTag t ON str.tag_id = t.tag_id
                WHERE {tag_conditions}
            """)
            total = session.execute(count_query, tag_params).scalar()

            image_list = []
            for img in images:
                image_list.append({
                    'id': img[0],
                    'url': img[1],
                    'name': img[2],
                    'description': img[3],
                    'source_type': img[4],
                    'is_downloaded': img[5],
                    'local_path': img[6]
                })

            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()

    @staticmethod
    def search_images_by_name_and_tags_order_by_time(name, tagli, page=1, per_page=100):
        """根据名称和标签搜索图片
        参数：
        - name: 名称
        - tagli: 标签列表
        - page: 页码
        - per_page: 每页数量
        返回格式: {
            'total': 总结果数,
            'images': [
                {'id': 图片ID, 'url': 图片URL, 'name': 标题, 'description': 描述},
                ...
            ]
        }
        """
        print(
            f"根据名称和标签搜索图片: name={name}, tagli={tagli}, page={page}, per_page={per_page}")
        session = DatabaseAPI.get_session()
        try:
            offset = (page - 1) * per_page

            # 构建标签条件
            tag_conditions = " OR ".join([f"t.tag = :tag{i}" for i in range(len(tagli))])
            tag_params = {f"tag{i}": tag for i, tag in enumerate(tagli)}

            query = text(f"""
                SELECT si.source_id, si.url, s.name, s.description, s.source_type, si.is_downloaded, si.local_path, s.release_date
                FROM SourceImage si
                JOIN Source s ON si.source_id = s.source_id
                JOIN SourceTagRelation str ON s.source_id = str.source_id
                JOIN SourceTag t ON str.tag_id = t.tag_id
                WHERE s.name LIKE :name AND ({tag_conditions})
                ORDER BY s.release_date DESC
                LIMIT :limit OFFSET :offset
            """)

            images = session.execute(query, {
                "name": f"%{name}%",
                **tag_params,
                "limit": per_page,
                "offset": offset
            }).fetchall()

            count_query = text(f"""
                SELECT COUNT(DISTINCT si.source_id)
                FROM SourceImage si
                JOIN Source s ON si.source_id = s.source_id
                JOIN SourceTagRelation str ON s.source_id = str.source_id
                JOIN SourceTag t ON str.tag_id = t.tag_id
                WHERE s.name LIKE :name AND ({tag_conditions})
            """)
            total = session.execute(count_query, {
                "name": f"%{name}%",
                **tag_params
            }).scalar()

            image_list = []
            for img in images:
                image_list.append({
                    'id': img[0],
                    'url': img[1],
                    'name': img[2],
                    'description': img[3],
                    'source_type': img[4],
                    'is_downloaded': img[5],
                    'local_path': img[6]
                })

            return {
                'total': total,
                'images': image_list
            }
        finally:
            session.close()
    
    @staticmethod
    def get_spider_para(name):
        """获取爬虫参数列表
        参数：
        - name: 爬虫名称
        返回：爬虫request_id_para参数列表
        """
        print(f"获取爬虫参数列表: name={name}")
        session = DatabaseAPI.get_session()
        try:
            query = text("""
                        SELECT s.request_id_para
                        FROM spider s
                        WHERE s.name = :name
                    """)
            para = session.execute(query, {"name": name}).fetchone()

            return para[0]
        finally:
            session.close()
    
    @staticmethod
    def delete_extired_spider():
        """每次调用时检查spider表中所有status为expired的爬虫并将这一行删除
        返回：True
        """
        print("删除过期爬虫")
        session = DatabaseAPI.get_session()
        try:
            # 删除所有状态为expired的爬虫
            query = text("""
                DELETE FROM Spider
                WHERE status = 'expired'
            """)
            
            try:
                result = session.execute(query)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"删除过期爬虫失败: {str(e)}")
                return False
        finally:
            session.close()

    