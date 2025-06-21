import mysql.connector  # MySQL数据库连接
from mysql.connector import Error
import configparser

def load_db_config(config_file='config.ini'):
    """
    从配置文件中读取数据库配置
    
    参数:
        config_file (str): 配置文件路径，默认为'config.ini'
        
    返回:
        dict: 包含数据库配置的字典
    """
    # 初始化配置解析器
    config = configparser.ConfigParser()
    
    # 读取配置文件
    config.read(config_file)
    
    # 创建配置字典
    DB_CONFIG = {
        'host': config.get('DATABASE', 'host', fallback='localhost'),
        'user': config.get('DATABASE', 'user', fallback='user'),
        'password': config.get('DATABASE', 'password', fallback='password'),
        'database': config.get('DATABASE', 'database', fallback=None),
        'port': config.getint('DATABASE', 'port', fallback=3306)
    }
    
    return DB_CONFIG


def create_database_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_database_and_tables(connection):
    try:
        cursor = connection.cursor()
        # 创建数据库
        cursor.execute("CREATE DATABASE if not exists anime")
        cursor.execute("USE anime")

        # 创建Website表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Website (
                website_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                base_url VARCHAR(255) NOT NULL,
                description TEXT
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        # 创建spider表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spider (
                spider_id INT PRIMARY KEY AUTO_INCREMENT,
                website_id INT NOT NULL DEFAULT 1,
                name CHAR(20) NOT NULL UNIQUE,
                download_to_local BOOLEAN DEFAULT FALSE,
                request_id_para TEXT,
                cookies VARCHAR(255),
                status ENUM('active', 'inactive', 'expired') DEFAULT 'active',
                FOREIGN KEY (website_id) REFERENCES Website(website_id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        # 创建Source表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Source (
                source_id INT AUTO_INCREMENT PRIMARY KEY,
                source_type ENUM('animation', 'book', 'game') DEFAULT 'animation' NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                author VARCHAR(100),
                studio VARCHAR(100),
                release_date DATE,
                status ENUM('not_released', 'ongoing', 'ended'),
                UNIQUE(source_type, name)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        cursor.execute("CREATE FULLTEXT INDEX idx_source_name ON Source(name) WITH PARSER ngram")
        cursor.execute("CREATE INDEX idx_source_release_date ON Source(release_date)")
        
        # 创建SourceImage表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SourceImage (
                image_id INT AUTO_INCREMENT PRIMARY KEY,
                url VARCHAR(255) NOT NULL UNIQUE,
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
        cursor.execute("CREATE INDEX idx_sourcetag_tag ON SourceTag(tag)")
        
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
        cursor.execute("CREATE INDEX idx_sourcetagrelation_source_tag ON SourceTagRelation(source_id,tag_id)")
        
        # 创建Role表
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
        cursor.execute("CREATE FULLTEXT INDEX idx_role_name ON Role(name) WITH PARSER ngram")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleTag (
                tag_id INT PRIMARY KEY AUTO_INCREMENT, 
                tag CHAR(20) NOT NULL UNIQUE,
                num INT NOT NULL
            )CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        cursor.execute("CREATE INDEX idx_roletag_tag ON RoleTag(tag)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleTagRelation(
                tag_id INT NOT NULL,
                role_id INT NOT NULL,
                PRIMARY KEY (role_id, tag_id),
                FOREIGN KEY (tag_id) REFERENCES RoleTag(tag_id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES Role(role_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX idx_roletagrelation_role_tag ON RoleTagRelation(role_id,tag_id)")

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
        cursor.execute("CREATE INDEX idx_rolesourcerelation_source_role ON RoleSourceRelation(source_id, role_id)")
        
        # 创建RoleImage表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoleImage (
                image_id INT AUTO_INCREMENT PRIMARY KEY,
                image_url VARCHAR(255) NOT NULL UNIQUE,
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
                original_url VARCHAR(255) NOT NULL UNIQUE
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
        cursor.execute("CREATE INDEX idx_linksonpage_source_link ON LinksOnPage(source_id, link_id)")

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



def main():
    
    # 创建数据库连接
    connection = create_database_connection()
    if not connection:
        print("Failed to connect to database. Exiting...")
        return
    
    try:
        # 创建表
        create_database_and_tables(connection)

    except Error as e:
        print(f"Error in main: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            print("Database connection closed")

if __name__ == "__main__":  
    DB_CONFIG = load_db_config()
    main()
    print("Database initialized successfully")