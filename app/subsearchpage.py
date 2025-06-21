from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QGridLayout)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPixmap, QIntValidator
from qfluentwidgets import (SearchLineEdit, PushButton, ScrollArea, 
                           PixmapLabel, BodyLabel, TitleLabel, LineEdit, 
                           Pivot, SegmentedWidget, ImageLabel, ComboBox, 
                           IndeterminateProgressRing, InfoBarIcon, InfoBar, InfoBarPosition, InfoBarManager, 
                           SmoothScrollArea)
from qfluentwidgets import FluentIcon as FIF
from .imagecard import ImageCard
from .tagselector import TagSelector
from .databaseapi import DatabaseAPI

# 搜索结果页面
class SubSearchPage(QWidget):
    def __init__(self, imgtype=1, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.per_page = 15  # 每页显示的数量
        self.current_name = ""
        self.current_tags = []
        self.total_items = 0  # 总结果数
        self.imgtype = imgtype
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 20)
        layout.setSpacing(5)

        # 搜索框和标签选择器容器
        self.search_container = QWidget()
        self.search_container_layout = QVBoxLayout(self.search_container)
        self.search_container_layout.setContentsMargins(0, 0, 0, 0)
        self.search_container_layout.setSpacing(5)
        
        # 搜索框
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("输入名字搜索")
        self.search_box.setFixedWidth(400)
        self.search_box.searchButton.clicked.connect(self.do_search)
        self.search_box.returnPressed.connect(self.do_search)

        if self.imgtype == 2:
            # 添加ComboBox
            self.sort_combo = ComboBox(self)
            self.sort_combo.addItems(['默认', '按照时间'])
            self.sort_combo.setCurrentIndex(0)
            self.sort_combo.setFixedWidth(120)  # 设置一个合适的宽度
        
        # 标签选择
        self.tags = DatabaseAPI.get_tags_list(self.imgtype)
        self.tag_selector = TagSelector(self.tags, self)
        self.tag_selector.signals.tags_changed.connect(self.handle_tags_changed)

        self.search_container_layout.addWidget(self.search_box, 0, Qt.AlignHCenter)
        if self.imgtype == 2:
            self.search_container_layout.addWidget(self.sort_combo, 0, Qt.AlignRight)
        self.search_container_layout.addWidget(self.tag_selector)
        
        # 搜索结果区域
        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAttribute(Qt.WA_StyledBackground)

        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 20, 0, 20)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        
        # 分页控件
        self.page_widget = QWidget()
        page_layout = QHBoxLayout(self.page_widget)
        page_layout.setContentsMargins(0, 5, 0, 5)
        
        self.prev_btn = PushButton("<", self)
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.prev_page)
        
        # 页码输入框
        self.page_edit = LineEdit(self)
        self.page_edit.setFixedWidth(60)
        self.page_edit.setAlignment(Qt.AlignCenter)
        self.page_edit.setValidator(QIntValidator(1, 9999))  # 只允许输入数字
        self.page_edit.returnPressed.connect(self.jump_to_page)
        
        # 总页数标签
        self.total_label = BodyLabel("/ 1", self)
        self.total_pages = 1
        self.current_page = 1

        self.next_btn = PushButton(">", self)
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_page)
        
        page_layout.addStretch()
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.page_edit)
        page_layout.addWidget(self.total_label)
        page_layout.addWidget(self.next_btn)
        page_layout.addStretch()
        
        layout.addWidget(self.search_container)
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.page_widget)
        
    def do_search(self):
        self.current_name = self.search_box.text()
        self.current_page = 1
        self.search_results()
        
    def search_results(self, clear=False):
        """执行搜索并加载第一页结果"""
        if clear:
            self.current_name = ""
            if self.imgtype == 2:
                self.sort_combo.setCurrentIndex(0)
            self.current_tags = []
            self.search_box.setText("")
            self.tag_selector.clear()
            self.current_page = 1
            self.total_items = 0
            self.total_pages = 1
            self.update_page_controls()
            for i in reversed(range(self.scroll_layout.count())): 
                self.scroll_layout.itemAt(i).widget().setParent(None)
            return 
        # 从数据库获取结果（只获取当前页）
        if self.imgtype == 2 and self.sort_combo.currentIndex() == 1:
                if self.current_name == "" and len(self.current_tags) == 0:
                    result = DatabaseAPI.fetch_all_images_order_by_time(
                        page=self.current_page, 
                        per_page=self.per_page
                    )
                elif self.current_name != "" and len(self.current_tags) == 0:
                    result = DatabaseAPI.search_images_by_name_order_by_time(
                        name=self.current_name,
                        page=self.current_page,
                        per_page=self.per_page
                    )
                elif self.current_name == "" and len(self.current_tags) != 0:
                    result = DatabaseAPI.search_images_by_tags_order_by_time(
                        tagli=self.current_tags,
                        page=self.current_page,
                        per_page=self.per_page
                    )
                else:
                    result = DatabaseAPI.search_images_by_name_and_tags_order_by_time(
                        name=self.current_name,
                        tagli=self.current_tags,
                        page=self.current_page,
                        per_page=self.per_page
                    )
        else:
            if self.current_name == "" and len(self.current_tags) == 0:
                result = DatabaseAPI.fetch_all_images(
                    page=self.current_page, 
                    per_page=self.per_page,
                    imgtype=self.imgtype
                )
            elif self.current_name != "" and len(self.current_tags) == 0:
                result = DatabaseAPI.search_images_by_name(
                    name=self.current_name,
                    page=self.current_page,
                    per_page=self.per_page,
                    imgtype=self.imgtype
                )
            elif self.current_name == "" and len(self.current_tags) != 0:
                result = DatabaseAPI.search_images_by_tags(
                    tagli=self.current_tags,
                    page=self.current_page,
                    per_page=self.per_page,
                    imgtype=self.imgtype
                )
            else:
                result = DatabaseAPI.search_images_by_name_and_tags(
                    name=self.current_name,
                    tagli=self.current_tags,
                    page=self.current_page,
                    per_page=self.per_page,
                    imgtype=self.imgtype
                )
        
        self.total_items = result['total']
        self.total_pages = (self.total_items + self.per_page - 1) // self.per_page
        
        # 加载当前页结果
        self.load_results(result['images'])
        
    def load_results(self, images):
        """加载搜索结果到界面"""
        # 清空现有结果
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)
        
        # 显示结果 (3行5列)
        for i, image_data in enumerate(images):
            row = i // 5
            col = i % 5
            card = ImageCard(image_data, self.imgtype, self.scroll_content)
            main_window = self.window()  # 获取最顶层的窗口
            if self.imgtype == 1:
                card.clicked.connect(main_window.show_image_detail_role)
            else:
                card.clicked.connect(main_window.show_image_detail_source)
            self.scroll_layout.addWidget(card, row, col, Qt.AlignCenter)
        
        # 更新分页状态
        self.update_page_controls()
        
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.search_results()
            
    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.search_results()

    def jump_to_page(self):
        """跳转到指定页码"""
        page_text = self.page_edit.text()
        if not page_text:
            return
            
        page = int(page_text)
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.search_results()
        else:
            # 显示错误提示
            self.createErrorInfoBar()

    def update_page_controls(self):
        """更新分页控件状态"""
        self.page_edit.setText(str(self.current_page))
        self.total_label.setText(f"/ {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
    
    def createErrorInfoBar(self):
        InfoBar.error(
            title='Error',
            content="Page not found",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,    # won't disappear automatically
            parent=self
        )

    def handle_tags_changed(self, tagli):
        """处理标签变化的槽函数"""
        self.current_tags = tagli
        self.current_page = 1
        self.search_results()