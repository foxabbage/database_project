# 项目文档

## 目录结构

```txt
主文件夹/
├── app/
│ ├── 页面组件
│ └── 数据库接口
├── resources/
│ ├── default_image.jpg
│ ├── anime.sql
│ ├── 项目文档.pdf
│ └── ER.png
├── kirakiradokidoki/
│ └── 爬虫组件
├── init.py
├── main_window.py
├── config.ini
└── requirements.txt
```

## 组件说明

### 1. app/

- **页面组件**：包含四个主要页面
  - `searchpage.py` - 搜索页面
  - `detailpage.py` - 详情页面
  - `tagpage.py` - 标签页面
  - `settingpage.py` - 设置页面
  - 以及相关子组件

- **数据库接口**
  - `databaseapi.py` - 为前端提供数据库操作接口

### 2. resources/

- `default_image.jpg` - 详情页默认图片
- `anime.sql` - 数据库数据
- `项目文档.pdf` - 项目文档
- `ER.png` - 数据库ER图，在不清晰时可以查看

### 3. kirakiradokidoki/

- **爬虫组件**
  - `add_single_source.py` - 主程序调用的爬虫模块
    - 功能：读取数据库爬虫数据并爬取/清洗条目数据
    - 输入：Bangumi 6位ID的字符串列表

### 4. 其他文件

- `init.py` - 数据库初始化脚本
- `main_window.py` - 前端主窗口程序
- `config.ini` - 数据库配置文件
- `requirements.txt` - 依赖库列表

## 使用说明

### 系统要求

- windows 10+
- Python 3.11+
- MySQL 8.0+

### 初始化步骤

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 修改 `config.ini` 文件中的数据库连接信息。(改为你的数据库的user和password)

3. 运行 `init.py` 初始化数据库。(该数据库名为anime，请注意不要有同名数据库存在)/或者可以通过创建名为anime的数据库并导入resources/anime.sql文件来初始化数据库。

4. 运行 `main_window.py` 启动前端程序。

5. 数据库具体设计，程序具体设计以及用户操作手册详见resources/项目文档.pdf。

## 小组分工

- 鉴于小组分工已经在项目文档中提及，此处为确保隐私，不再罗列，请参考提交于Elearning的项目文档。
