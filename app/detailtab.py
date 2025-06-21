from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,  
                               QPushButton, QGridLayout)
from PySide6.QtCore import Qt, QEasingCurve, Signal
from PySide6.QtGui import QPainter, QPainterPath, QIcon
from qfluentwidgets import (PushButton, ScrollArea, 
                           BodyLabel, TitleLabel, LineEdit, SubtitleLabel, PrimaryPushButton, IconWidget, 
                           Pivot, SegmentedWidget, ImageLabel, FlowLayout, PushButton, MessageBox, MessageBoxBase,  
                           IndeterminateProgressRing, HorizontalPipsPager, PipsScrollButtonDisplayMode, IndeterminateProgressBar, 
                           setTheme, Theme, SmoothScrollArea, TitleLabel, BodyLabel, FluentStyleSheet, 
                           TransparentToolButton, TextEdit, InfoBar, InfoBarPosition, ToolButton, 
                           setFont, FluentIconBase, drawIcon, isDarkTheme, Theme, themeColor, 
                           HyperlinkButton)
from qfluentwidgets import FluentIcon as FIF
from .databaseapi import DatabaseAPI
from .imageloader import ImageLoader
from bs4 import BeautifulSoup
from .tagadder import TagAdder
from .deletemessagebox import *
import datetime
import re

class SmoothScrollPix(SmoothScrollArea):

    def __init__(self, pmap):
        super().__init__()
        self.label = ImageLabel(self)
        self.label.setPixmap(pmap)

        # customize scroll animation
        self.setScrollAnimation(Qt.Vertical, 200, QEasingCurve.OutQuint)
        self.setScrollAnimation(Qt.Horizontal, 200, QEasingCurve.OutQuint)

        #self.horizontalScrollBar().setValue(1900)
        self.setWidget(self.label)

        self.setStyleSheet("""
            QScrollArea {
            border: none;
            }
        """)

class ClickableImageLabel(ImageLabel):
    """支持点击后在新窗口显示原图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setScaledContents(False)
        self.original_map = None
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton and not self.isNull():
            self.showOriginalImage()
    
    def mouseReleaseEvent(self, e):
        '''覆盖鼠标释放事件，防止报错'''
        pass

    def scale_image_to_label(self):
        """
        将图片缩放到适合标签的大小范围，保持宽高比和平滑缩放
        
        参数:
            image_path: 图片文件路径
            
        返回:
            缩放后的QPixmap对象
        """
        if self.isNull():
            return

        original_pixmap = self.pixmap()
        self.original_map = original_pixmap
        
        # 获取原始尺寸
        original_width = original_pixmap.width()
        original_height = original_pixmap.height()
        original_ratio = original_width / original_height

        if original_height > 360:
            target_height = 360
            target_width = int(target_height * original_ratio)
        elif original_height < 200:
            target_height = 200
            target_width = int(target_height * original_ratio)
        else:
            target_height = original_height
            target_width = original_width
        
        # 使用平滑变换进行缩放
        scaled_pixmap = original_pixmap.scaled(
            target_width, target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
        self.setFixedSize(target_width, target_height)
        
    def showOriginalImage(self):
        """在新窗口中显示原始图像"""
        height = self.original_map.height()
        width = self.original_map.width()
        # 创建新窗口
        self.viewer = QWidget()
        self.viewer.setWindowTitle("origin")
        if height > width:
            if height > 1000:
                self.viewer.resize(width+30, 1000)
            else:
                self.viewer.resize(width+30, height+30)
        else:
            if width > 1000:
                self.viewer.resize(1000, height+30)
            else:
                self.viewer.resize(width+30, height+30)
        
        
        # 创建内容页面
        layout = QVBoxLayout(self.viewer)
        layout.setContentsMargins(0, 0, 0, 0)
        image_label = SmoothScrollPix(self.original_map)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        
        # 设置窗口内容
        self.viewer.show()

class InterHyperlinkButtonRole(PushButton):
    def __init__(self, image_id: int, text: str, parent=None, main_window=None):
        super().__init__(parent)
        FluentStyleSheet.BUTTON.apply(self)
        self.setCursor(Qt.PointingHandCursor)
        setFont(self)
        self.image_id = image_id
        self.setText(text)
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        self._main_window = self.window()
        self._main_window.show_image_detail_source(self.image_id)
    
    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            icon = icon.icon(color=themeColor())
        elif not self.isEnabled():
            painter.setOpacity(0.3628 if isDarkTheme() else 0.36)

        drawIcon(icon, painter, rect, state)

class InterHyperlinkButtonSource(PushButton):
    def __init__(self, image_id: int, text: str, parent=None, main_window=None):
        super().__init__(parent)
        FluentStyleSheet.BUTTON.apply(self)
        self.setCursor(Qt.PointingHandCursor)
        setFont(self)
        self.image_id = image_id
        self.setText(text)
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        self._main_window = self.window()
        self._main_window.show_image_detail_role(self.image_id)
    
    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            icon = icon.icon(color=themeColor())
        elif not self.isEnabled():
            painter.setOpacity(0.3628 if isDarkTheme() else 0.36)

        drawIcon(icon, painter, rect, state)

class TagAdderMessageBox(MessageBoxBase):
    """标签添加对话框"""
    yesSignal = Signal(list)
    cancelSignal = Signal()
    def __init__(self, tagli, parent=None):
        super().__init__(parent)
        self.tagadder = TagAdder(tagli)
        self.viewLayout.addWidget(self.tagadder)
        # 隐藏按钮
        self.cancelButton.setText('取消')
        self.yesButton.setText('确定')
        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)
        
        # 设置对话框样式
        self.widget.setMinimumWidth(350)
    
    def __onYesButtonClicked(self):
        self.accept()
        self.yesSignal.emit(list(self.tagadder.selected_tags.keys()))
    
    def __onCancelButtonClicked(self):
        self.reject()
        self.cancelSignal.emit()


# 图片详情页面
class DetailTab(QWidget):
    def __init__(self, image_id, imgtype=1, parent=None):
        super().__init__(parent)
        self.image_type = imgtype
        if imgtype == 1:
            self.details = DatabaseAPI.get_image_details_role(image_id)
            self.image_li = DatabaseAPI.get_image_list_role(image_id)
            self.image_num = len(self.image_li)
            self.tags = DatabaseAPI.get_tags_list_by_id(imgtype, image_id)
            self.sourceli = DatabaseAPI.get_source_of_role(image_id)
        else:
            self.details = DatabaseAPI.get_image_details_source(image_id)
            self.image_li = DatabaseAPI.get_image_list_source(image_id)
            self.image_num = len(self.image_li)
            self.tags = DatabaseAPI.get_tags_list_by_id(imgtype, image_id)
            self.external_link_li = DatabaseAPI.get_external_link_list(image_id)
            self.roleli = DatabaseAPI.get_role_list(image_id)
        self.tags = set(self.tags)

        # 主布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        # 可滚动的区域（占满剩余空间）
        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setWidgetResizable(True)
        #self.scroll_area.enableTransparentBackground()
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setAttribute(Qt.WA_StyledBackground)

        # 滚动区域的内容容器
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(30, 10, 30, 10)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignTop)  # 内容顶部对齐

        # 1. 顶部图片
        self.image_label = ClickableImageLabel(self.scroll_content)
        self.image_label.scale_image_to_label()
        self.image_label.setScaledContents(True)
        self.loading_indicator = IndeterminateProgressRing(self.scroll_content)
        self.loading_indicator.setFixedSize(80, 80)
        self.scroll_layout.addWidget(self.loading_indicator, 0, 0, Qt.AlignHCenter)
        self.scroll_layout.addWidget(self.image_label, 1, 0, Qt.AlignHCenter)

        self.pager = HorizontalPipsPager(self.scroll_content)
        self.pager.setPageNumber(self.image_num)
        self.pager.setVisibleNumber(min(self.image_num, 5))
        self.pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.pager.currentIndexChanged.connect(self.on_page_changed)
        self.scroll_layout.addWidget(self.pager, 2, 0, Qt.AlignHCenter)

        # 2. 姓名标题
        self.name_label = TitleLabel(self.details['name'], self)
        self.name_label.setAlignment(Qt.AlignLeft)
        self.name_label.setContentsMargins(0, 5, 0, 0)
        self.scroll_layout.addWidget(self.name_label, 3, 0)

        # 3. 简介文本
        self.tag_title = SubtitleLabel("简介", self)
        self.tag_title.setAlignment(Qt.AlignLeft)

        # 创建水平布局放置标题和编辑按钮
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        title_layout.addWidget(self.tag_title, alignment=Qt.AlignLeft)

        # 添加编辑按钮
        self.edit_button = TransparentToolButton(FIF.EDIT, self)
        self.edit_button.clicked.connect(self.toggle_editable)
        # 创建并添加取消按钮
        self.cancel_button = TransparentToolButton(FIF.CANCEL, self)
        self.cancel_button.clicked.connect(self.cancel_edits)
        self.cancel_button.setVisible(False)
        title_layout.addWidget(self.edit_button, alignment=Qt.AlignLeft)
        title_layout.addWidget(self.cancel_button, alignment=Qt.AlignLeft)
        title_layout.addStretch(1)

        # 将标题布局添加到scroll_layout
        title_widget = QWidget()
        title_widget.setLayout(title_layout)
        self.scroll_layout.addWidget(title_widget, 4, 0)

        # 创建富文本编辑框
        self.desc_textedit = TextEdit(self)
        self.desc_textedit.setContentsMargins(5, 5, 5, 5)
        self.desc_textedit.setReadOnly(True)  # 初始设置为只读
        self.desc_textedit.setHtml(self.format_details(imgtype))  # 使用格式化方法生成HTML内容
        self.scroll_layout.addWidget(self.desc_textedit, 5, 0)

        self.desc_textedit.setReadOnly(True)  # 初始设置为只读
        self.desc_textedit.setHtml(self.format_details(imgtype))  # 使用格式化方法生成HTML内容
        self.scroll_layout.addWidget(self.desc_textedit, 5, 0)

        # 4. 标签
        self.tag_title = SubtitleLabel("标签", self)
        self.tag_title.setAlignment(Qt.AlignLeft)
        self.tag_edit_mode = False
        self.removed_tags = set()  # 记录被移除的标签
        self.added_tags = set()    # 记录新增的标签

        # 创建水平布局放置标题和编辑按钮
        tag_title_layout = QHBoxLayout()
        tag_title_layout.setContentsMargins(0, 0, 0, 0)
        tag_title_layout.setSpacing(5)
        tag_title_layout.addWidget(self.tag_title, alignment=Qt.AlignLeft)

        # 添加编辑按钮
        self.tag_edit_button = TransparentToolButton(FIF.EDIT, self)
        self.tag_edit_button.clicked.connect(self.toggle_tag_editable)
        # 创建并添加取消按钮
        self.tag_cancel_button = TransparentToolButton(FIF.CANCEL, self)
        self.tag_cancel_button.clicked.connect(self.cancel_tag_edits)
        self.tag_cancel_button.setVisible(False)
        tag_title_layout.addWidget(self.tag_edit_button, alignment=Qt.AlignLeft)
        tag_title_layout.addWidget(self.tag_cancel_button, alignment=Qt.AlignLeft)
        tag_title_layout.addStretch(1)

        # 将标题布局添加到scroll_layout
        tag_title_widget = QWidget()
        tag_title_widget.setLayout(tag_title_layout)
        self.scroll_layout.addWidget(tag_title_widget, 6, 0)
        
        # Create a container widget for tags with FlowLayout
        self.tag_container = QWidget()
        self.tag_flow_layout = FlowLayout(self.tag_container)
        self.tag_flow_layout.setContentsMargins(10, 0, 10, 10)
        self.tag_flow_layout.setSpacing(0)
        
        # Add tags as PillPushButtons
        for tag in self.tags:
            tag_button = PushButton(tag)
            tag_button.setCheckable(True)
            tag_button.setChecked(True)  # Make it appear pressed
            tag_button.setEnabled(True)
            self.tag_flow_layout.addWidget(tag_button)
        self.scroll_layout.addWidget(self.tag_container, 7, 0)

        # 5. 外部链接
        if imgtype == 1:
            self.link_title = SubtitleLabel("来源链接", self)
            self.link_title.setAlignment(Qt.AlignLeft)
            self.scroll_layout.addWidget(self.link_title, 8, 0)
            self.links_container = QWidget()
            self.links_layout = FlowLayout(self.links_container)
            self.links_layout.setContentsMargins(10, 0, 10, 10)
            self.links_layout.setSpacing(5)  # 垂直间距更小

            for link in self.sourceli:
                link_button = InterHyperlinkButtonRole(link['source_id'], link['name'], self)
                link_button.setIcon(FIF.LINK)
                self.links_layout.addWidget(link_button)
            self.scroll_layout.addWidget(self.links_container, 9, 0)  # 添加到下一行

        elif imgtype == 2:
            start = 8
            if len(self.roleli) > 0:
                self.link_title = SubtitleLabel("角色链接", self)
                self.link_title.setAlignment(Qt.AlignLeft)
                self.scroll_layout.addWidget(self.link_title, 8, 0)
                self.links_container = QWidget()
                self.links_layout = FlowLayout(self.links_container)
                self.links_layout.setContentsMargins(10, 0, 10, 10)
                self.links_layout.setSpacing(5)  # 垂直间距更小

                for link in self.roleli:
                    link_button = InterHyperlinkButtonSource(link['role_id'], link['name'], self)
                    link_button.setIcon(FIF.LINK)
                    self.links_layout.addWidget(link_button)
                self.scroll_layout.addWidget(self.links_container, 9, 0)  # 添加到下一行
                start += 2
            if len(self.external_link_li) > 0:
                self.link_title = SubtitleLabel("外部链接", self)
                self.link_title.setAlignment(Qt.AlignLeft)
                self.scroll_layout.addWidget(self.link_title, start, 0)
                self.links_container = QWidget()
                self.links_layout = QVBoxLayout(self.links_container)
                self.links_layout.setContentsMargins(0, 0, 0, 0)
                self.links_layout.setSpacing(5)  # 垂直间距更小

                for link in self.external_link_li:
                    link_button = HyperlinkButton(link['original_url'], link['title'], self)
                    link_button.setIcon(FIF.LINK)
                    self.links_layout.addWidget(link_button, alignment=Qt.AlignLeft)  # 左对齐
                self.scroll_layout.addWidget(self.links_container, start+1, 0)  # 添加到下一行
        
        # Add delete button at bottom right
        self.delete_button = PrimaryPushButton('删除', self)
        self.delete_button.setIcon(FIF.DELETE)
        self.delete_button.clicked.connect(self.confirm_delete)
        
        # Create a container for the delete button to position it at bottom right
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addStretch(1)  # Push button to the right
        self.button_layout.addWidget(self.delete_button)
        
        # Add button container to main layout (at the bottom)
        self.scroll_layout.addWidget(self.button_container)

        # 设置滚动区域的内容
        self.scroll_area.setWidget(self.scroll_content)

        # 将滚动区域添加到主布局（stretch=1 使其占满剩余空间）
        self.layout.addWidget(self.scroll_area, 1)

        self.init_loader(self.image_li[0])
    
    def init_loader(self, image_data):
        """初始化图片加载器"""
        if image_data['is_downloaded']:
            self.loading_indicator.hide()
            self.image_label.setPixmap(image_data['local_path'])
            self.image_label.scale_image_to_label()
        else:
            self.loader = ImageLoader(self)
            self.loader.loaded.connect(self.on_image_loaded)
            self.loader.error.connect(self.on_load_error)
            self.loader.load(image_data['url'])
        
    def on_image_loaded(self, pixmap):
        """图片加载完成处理"""
        self.loading_indicator.hide()
        self.image_label.setPixmap(pixmap)
        self.image_label.scale_image_to_label()
        
    def on_load_error(self, error_msg):
        """图片加载失败处理"""
        self.loading_indicator.hide()
        self.image_label.setText("加载失败")
        print(error_msg)

    def on_page_changed(self, page):
        """页面切换处理"""
        self.image_label.setFixedSize(0, 0)
        self.image_label.clear()
        self.loading_indicator.show()
        self.init_loader(self.image_li[page])
    
    def toggle_editable(self):
        imgtype = self.image_type
        if self.desc_textedit.isReadOnly():
            # 切换到编辑模式
            self.desc_textedit.setReadOnly(False)
            self.desc_textedit.setHtml(self.format_details(imgtype))
            self.edit_button.setIcon(FIF.SAVE)
            self.cancel_button.setVisible(True)
            
        else:
            # 保存并切换回只读模式
            self.edit_button.setEnabled(False)
            self.save_edited_fields(imgtype)
            self.desc_textedit.setReadOnly(True)
            self.desc_textedit.setHtml(self.format_details(imgtype))
            self.cancel_button.setVisible(False)
            self.edit_button.setIcon(FIF.EDIT)
            self.edit_button.setEnabled(True)

    def format_details(self, imgtype):
        """格式化详情数据为HTML"""
        if imgtype == 1:
            # 获取详情数据
            gender = self.details.get('gender', 'unknown')
            if gender == 'male':
                gender = '男'
            elif gender == 'female':
                gender = '女'
            else:
                gender = '未知'
            birthday = self.details.get('birthday', '未知')
            birthday = birthday.strftime('%m-%d') if birthday else '未知'
            voice_actor = self.details.get('voice_actor', '未知')
            description = self.details.get('description', '暂无简介')
            
            # 创建HTML内容
            html = f"""
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 30%; padding: 5px; font-weight: bold;">性别:</td>
                    <td style="padding: 5px;">{gender}</td>
                </tr>
                <tr>
                    <td style="width: 30%; padding: 5px; font-weight: bold;">生日:</td>
                    <td style="padding: 5px;">{birthday}</td>
                </tr>
                <tr>
                    <td style="width: 30%; padding: 5px; font-weight: bold;">声优:</td>
                    <td style="padding: 5px;">{voice_actor}</td>
                </tr>
            </table>
            <hr>
            <p style="margin-bottom: 10px; margin-left: 5px; margin-right: 5px;">{description}</p>
            """
            return html
        else:
            # 获取详情数据
            author = self.details.get('author', '未知')
            studio = self.details.get('studio', '未知')
            release_date = self.details.get('release_date', '未知')
            release_date = release_date.strftime('%Y-%m-%d') if release_date else '未知'
            status = self.details.get('status', '未知')
            if status == 'ongoing':
                status = '连载中'
            elif status == 'ended':
                status = '完结'
            elif status == 'not_released':
                status = '未上映'
            description = self.details.get('description', '暂无简介')

            # 创建HTML内容
            html = f"""
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 30%; padding: 5px; font-weight: bold;">作者:</td>
                    <td style="padding: 5px;">{author}</td>
                </tr>
                <tr>
                    <td style="width: 30%; padding: 5px; font-weight: bold;">工作室:</td>
                    <td style="padding: 5px;">{studio}</td>
                </tr>
                <tr>
                    <td style="width: 30%; padding: 5px; font-weight: bold;">发布日期:</td>
                    <td style="padding: 5px;">{release_date}</td>
                </tr>
                <tr>
                    <td style="width: 30%; padding: 5px; font-weight: bold;">状态:</td>
                    <td style="padding: 5px;">{status}</td>
                </tr>
            </table>
            <hr>
            <p style="margin-bottom: 10px; margin-left: 5px; margin-right: 5px;">{description}</p>
            """
            return html
    
    def save_edited_fields(self, imgtype):
        """使用BeautifulSoup按顺序从HTML中提取编辑后的字段值"""
        html = self.desc_textedit.toHtml()
        soup = BeautifulSoup(html, 'html.parser')
        bd_try_flag = 0

        if imgtype == 1:
            # 提取表格中的属性值（按顺序）
            table_rows = soup.find_all('tr')
            if len(table_rows) >= 3:
                # 第一行是性别
                gender_td = table_rows[0].find_all('td')
                if len(gender_td) >= 2:
                    self.details['gender'] = gender_td[1].get_text(strip=True)
                    if self.details['gender'] == '男' or self.details['gender'] == 'male':
                        self.details['gender'] = 'male'
                    elif self.details['gender'] == '女' or self.details['gender'] == 'female':
                        self.details['gender'] = 'female'
                    else:
                        self.details['gender'] = 'unknown'
                
                # 第二行是生日
                birthday_td = table_rows[1].find_all('td')
                if len(birthday_td) >= 2:
                    temp = self.details['birthday']
                    try:
                        date_str = birthday_td[1].get_text(strip=True)
                        date_str = date_str.replace(' ', '')
                        if date_str == '未知' or date_str == 'unknown':
                            self.details['birthday'] = None
                        else:
                            match = re.match(r"(\d{1,2})\s*-\s*(\d{1,2})", date_str)
                            mm, dd = match.groups()
                            datetime_str = f"2000-{mm}-{dd}"
                            self.details['birthday'] = datetime.datetime.strptime(datetime_str, '%Y-%m-%d')
                    except:
                        self.createDayErrorInfoBar()
                        bd_try_flag = 1
                        self.details['birthday'] = temp
                
                # 第三行是声优
                voice_actor_td = table_rows[2].find_all('td')
                if len(voice_actor_td) >= 2:
                    self.details['voice_actor'] = voice_actor_td[1].get_text(strip=True)
                
        else:
            # 提取表格中的属性值（按顺序）
            table_rows = soup.find_all('tr')
            if len(table_rows) >= 4:
                # 第一行是作者
                author_td = table_rows[0].find_all('td')
                if len(author_td) >= 2:
                    self.details['author'] = author_td[1].get_text(strip=True)

                # 第二行是工作室
                studio_td = table_rows[1].find_all('td')
                if len(studio_td) >= 2:
                    self.details['studio'] = studio_td[1].get_text(strip=True)

                # 第三行是发布日期
                release_date_td = table_rows[2].find_all('td')
                if len(release_date_td) >= 2:
                    temp = self.details['release_date']
                    release_date = release_date_td[1].get_text(strip=True)
                    release_date = release_date.replace(' ', '')
                    try:
                        if release_date == '未知' or release_date == 'unknown':
                            self.details['release_date'] = None
                        else:
                            self.details['release_date'] = datetime.datetime.strptime(release_date, '%Y-%m-%d')
                    except:
                        self.createDayErrorInfoBar()
                        bd_try_flag = 1
                        self.details['release_date'] = temp

                # 第四行是状态
                status_td = table_rows[3].find_all('td')
                if len(status_td) >= 2:
                    temp = self.details['status']
                    status_text = status_td[1].get_text(strip=True)
                    if status_text == '放送中' or status_text == '连载中' or status_text == '放送' or status_text == '连载' or status_text == 'ongoing':
                        self.details['status'] = 'ongoing'
                    elif status_text == '完结' or status_text == '已完结' or status_text == 'ended':
                        self.details['status'] = 'ended'
                    elif status_text == '未放送' or status_text == '未上映' or status_text == '未发布' or status_text == 'not_released':
                        self.details['status'] = 'not_released'
                    else:
                        self.createStatusInputErrorInfoBar()
                        bd_try_flag = 1
                        self.details['status'] = temp
        
        # 提取描述（hr标签后的第一个p标签）
        hr_tag = soup.find('hr')
        if hr_tag:
            p_tags = hr_tag.find_all_next('p')
            if p_tags:
                # 提取每个<p>标签的内容并用<br>连接
                self.details['description'] = '<br>'.join(p.decode_contents() for p in p_tags)
            else:
                self.details['description'] = ''
        
        # 保存到数据库
        if bd_try_flag == 1:
            return
        self.save_details_to_database(self.image_type)

    def save_details_to_database(self, imgtype):
        # 这里可以添加保存到数据库的操作
        rowcount = DatabaseAPI.save_details_to_database(self.details, imgtype)
        if rowcount == 1:
            self.createSavedSuccessInfoBar()
        else:
            self.createSavedErrorInfoBar()
    
    def cancel_edits(self):
        imgtype = self.image_type
        self.desc_textedit.setReadOnly(True)
        self.desc_textedit.setHtml(self.format_details(imgtype))
        self.cancel_button.setVisible(False)
        self.edit_button.setIcon(FIF.EDIT)
        self.edit_button.setEnabled(True)
            
    def createSavedErrorInfoBar(self):
        InfoBar.error(
            title='Error',
            content="Save failed, please try again",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )
    
    def createDayErrorInfoBar(self):
        InfoBar.error(
            title='Error',
            content="please input birthday like mm-dd, and release date like yyyy-mm-dd",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )
    
    def createStatusInputErrorInfoBar(self):
        InfoBar.error(
            title='Error',
            content="please input status like 未发布、连载、完结",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )
    
    def createSavedSuccessInfoBar(self):
        InfoBar.success(
            title='Success',
            content="Save successfully",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,    # disappear after 2 seconds
            parent=self
        )
    
    def toggle_tag_editable(self):
        """切换标签编辑模式"""
        # 切换编辑模式
        self.tag_edit_mode = not self.tag_edit_mode
        
        if self.tag_edit_mode:
            # 进入编辑模式
            self.tag_edit_button.setIcon(FIF.SAVE)  # 切换为保存图标
            self.tag_cancel_button.setVisible(True)
            
            # 移除所有现有标签按钮并重新添加为可编辑版本
            self.tag_flow_layout.takeAllWidgets()
                
            for tag in self.tags:
                tag_button = PushButton(tag)
                tag_button.setCheckable(False)
                tag_button.clicked.connect(lambda _, t=tag: self.remove_tag(t))
                self.tag_flow_layout.addWidget(tag_button)
            
            # 添加加号按钮
            self.add_add_tag_button()
            
        else:
            # 退出编辑模式，保存更改
            self.tag_edit_button.setEnabled(False)
            self.tag_cancel_button.setVisible(False)
            
            self.tag_flow_layout.takeAllWidgets()
            # 更新数据库
            self.update_tags_in_database()
            
            # 更新标签列表
            self.update_tag_list()
            
            # 清除临时列表
            self.removed_tags = set()
            self.added_tags = set()
            
            # 重新加载显示标签（不可编辑状态）
            for tag in self.tags:
                tag_button = PushButton(tag)
                tag_button.setCheckable(True)
                tag_button.setChecked(True)
                tag_button.setEnabled(True)
                self.tag_flow_layout.addWidget(tag_button)
            self.tag_edit_button.setIcon(FIF.EDIT)  # 切换回编辑图标
            self.tag_edit_button.setEnabled(True)

    def add_add_tag_button(self):
        """添加加号按钮"""
        self.add_button = ToolButton(FIF.ADD)
        self.add_button.clicked.connect(self.show_tag_selector)
        self.tag_flow_layout.addWidget(self.add_button)

    def remove_tag(self, tag):
        """移除标签"""
        # 从布局中移除对应的按钮
        for i in range(self.tag_flow_layout.count()):
            widget = self.tag_flow_layout.itemAt(i).widget()
            if hasattr(widget, 'text') and widget.text() == tag:
                widget = self.tag_flow_layout.takeAt(i)
                if widget:
                    widget.deleteLater()
                break
        
        self.tag_flow_layout.update()

        # 如果标签是原有的，添加到移除列表；如果是新增的，从新增列表移除
        if tag in self.tags:
            self.removed_tags.add(tag)
        elif tag in self.added_tags:
            self.added_tags.remove(tag)

    def show_tag_selector(self):
        """显示标签选择器"""
        # 假设你已经有一个标签选择器widget，名为tag_selector_widget
        # 并且它会发出一个tag_selected信号
        tags_all = DatabaseAPI.get_tags_list(self.image_type)
        _main_window = self.window()
        self.tag_selector_widget = TagAdderMessageBox(tags_all, _main_window)
        self.tag_selector_widget.yesSignal.connect(self.add_new_tag_li)
        self.tag_selector_widget.cancelSignal.connect(lambda: None)
        self.tag_selector_widget.show()

    def add_new_tag_li(self, tagli):
        """添加新标签"""
        # 避免重复添加
        if len(tagli) == 0:
            return
        for tag in tagli:
            self.add_new_tag(tag)

    def add_new_tag(self, tag):
        """添加新标签"""
        # 避免重复添加
        if tag in self.tags or tag in self.added_tags:
            return
        
        # 在加号按钮前添加新标签
        button_count = self.tag_flow_layout.count()
        insert_position = button_count - 1  # 在加号按钮前插入
        
        tag_button = PushButton(tag)
        tag_button.setCheckable(False)
        tag_button.clicked.connect(lambda _, t=tag: self.remove_tag(t))
        
        # 在加号按钮前插入新标签
        self.tag_flow_layout.insertWidget(insert_position, tag_button)
        
        # 记录新增的标签
        self.added_tags.add(tag)

    def update_tags_in_database(self):
        """更新数据库中的标签"""
        del_rowcount = 0
        add_rowcount = 0
        if len(self.removed_tags) != 0:
            del_rowcount = DatabaseAPI.delete_tags_by_id(self.removed_tags, self.details['id'], self.image_type)
        if len(self.added_tags) != 0:
            add_rowcount = DatabaseAPI.add_tags_by_id(self.added_tags, self.details['id'], self.image_type)
        if del_rowcount == len(self.removed_tags) and add_rowcount == len(self.added_tags):
            self.createSavedSuccessInfoBar()
        else:
            self.createSavedErrorInfoBar()

    def update_tag_list(self):
        """更新标签列表"""
        # 更新self.tags列表
        for tag in self.removed_tags:
            if tag in self.tags:
                self.tags.remove(tag)
        
        for tag in self.added_tags:
            if tag not in self.tags:
                self.tags.add(tag)
        _main_window = self.window()
        _main_window.refresh_tag_page()

    def cancel_tag_edits(self):
        self.tag_edit_mode = False
        self.tag_cancel_button.setVisible(False)
            
        self.tag_flow_layout.takeAllWidgets()
        
        # 清除临时列表
        self.removed_tags = set()
        self.added_tags = set()
            
        # 重新加载显示标签（不可编辑状态）
        for tag in self.tags:
            tag_button = PushButton(tag)
            tag_button.setCheckable(True)
            tag_button.setChecked(True)
            tag_button.setEnabled(True)
            self.tag_flow_layout.addWidget(tag_button)
        self.tag_edit_button.setIcon(FIF.EDIT)  # 切换回编辑图标

    def confirm_delete(self):
        """Show confirmation dialog before deleting"""
        title = "确认删除"
        content = f"确定要删除这个{'角色' if self.image_type == 1 else '来源'}吗？此操作不可撤销！"
        
        # Show confirmation dialog
        _main_window = self.window()
        msg_box = DeleteConfirmMessageBox(title, content, _main_window)
        msg_box.yesSignal.connect(self.execute_delete)
        msg_box.cancelSignal.connect(lambda: None)
        msg_box.show()

    def execute_delete(self):
        """Perform the actual deletion"""
        # Show progress dialog
        _main_window = self.window()
        processing_dialog = ProcessingMessageBox(
            "处理中", 
            "正在删除数据，请稍候...", 
            _main_window
        )
        processing_dialog.show()
        
        # Call database API to delete
        idlist = DatabaseAPI.delete_by_id(self.details['id'], self.image_type)
        if len(idlist) >= 0:
            # Close processing dialog
            processing_dialog.accept()
            
            # Show success message
            success_dialog = DeleteResultMessageBox(
                "删除成功", 
                "数据已成功删除", 
                _main_window
            )
            success_dialog.yesSignal.connect(lambda: self.close_tab())
            success_dialog.show()
            
        else:
            processing_dialog.accept()
            DeleteResultMessageBoxError(
                "删除失败", 
                f"删除过程中发生错误", 
                _main_window
            ).show()

    def close_tab(self):
        """Close this tab by calling parent's close_tab method"""
        _main_window = self.window()
        _main_window.refresh()
