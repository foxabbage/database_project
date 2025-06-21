from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QApplication
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from qfluentwidgets import (SmoothScrollArea, FlowLayout, PushButton, SearchLineEdit, PrimaryToolButton,
                            PushButton, LineEdit, BodyLabel, InfoBar, InfoBarPosition, MessageBoxBase, 
                            RoundMenu, Action, MenuAnimationType, TogglePushButton)
from .databaseapi import DatabaseAPI
from qfluentwidgets import FluentIcon as FIF
from .deletemessagebox import DeleteConfirmMessageBox

class SpiderPushButton(TogglePushButton):
    """爬虫按钮"""
    delete_signal = Signal(str)
    pause_signal = Signal(str)
    resume_signal = Signal(str)
    def __init__(self, text, status, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.status = status
        self.setStatus(status)
    
    def setStatus(self, status):
        """设置爬虫状态"""
        if status == "active":
            self.setChecked(True)
        elif status == "inactive":
            self.setChecked(False)
        else:  # "expired"
            self.setDisabled(True)
    
    def mousePressEvent(self, event):
        self.contextMenuEvent(event)
    
    def contextMenuEvent(self, e):
        menu = RoundMenu(parent=self)
        
        # 创建Copy主菜单项及其子菜单
        menu.addAction(Action(FIF.COPY, 'Copy', triggered = self.copy_to_clipboard))
        menu.addAction(Action(FIF.PAUSE, 'Pause', triggered = self.on_pause))
        menu.addAction(Action(FIF.PLAY, 'Resume', triggered = self.on_resume))
        menu.addAction(Action(FIF.CLOSE, 'Delete', triggered = self.on_delete))
        if self.status == "active":
            menu.actions()[1].setCheckable(True)
            menu.actions()[1].setChecked(True)
            menu.actions()[2].setDisabled(True)
        elif self.status == "inactive":
            menu.actions()[1].setDisabled(True)
            menu.actions()[2].setCheckable(True)
            menu.actions()[2].setChecked(True)
        menu.actions()[0].setCheckable(True)
        menu.actions()[0].setChecked(True)

        # 显示菜单
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def copy_to_clipboard(self):
        """将指定类型的数据复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text())
    
    def on_delete(self):
        self.delete_signal.emit(self.text())
    
    def on_pause(self):
        self.pause_signal.emit(self.text())

    def on_resume(self):
        self.resume_signal.emit(self.text())

class SubSpiderPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SubSpiderPage")
        self.per_page = 60
        self.spiders_status_total = DatabaseAPI.get_all_spiders_and_status(1, self.per_page)
        self.total_items = self.spiders_status_total['total']
        self.spiders_status = self.spiders_status_total['spiders_and_status']
        self.spiders = [spider['name'] for spider in self.spiders_status]
        self.current_text = ""
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 15, 0, 20)
        self.main_layout.setSpacing(10)
        
        # 滚动区域
        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 滚动区域的内容部件
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        
        # 流式布局
        self.flow_layout = FlowLayout(self.scroll_content)
        self.flow_layout.setContentsMargins(20, 20, 20, 20)
        self.flow_layout.setVerticalSpacing(20)
        self.flow_layout.setHorizontalSpacing(30)
        
        self.main_layout.addWidget(self.scroll_area)

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
        self.total_pages = (self.total_items + self.per_page - 1) // self.per_page
        self.total_label = BodyLabel(f"/ {self.total_pages}", self)
        self.current_page = 1
        self.page_edit.setText(str(self.current_page))

        self.next_btn = PushButton(">", self)
        if self.current_page == self.total_pages:
            self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_page)
        
        page_layout.addStretch()
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.page_edit)
        page_layout.addWidget(self.total_label)
        page_layout.addWidget(self.next_btn)
        page_layout.addStretch()
        
        self.main_layout.addWidget(self.page_widget)
        
        self.spider_buttons = []
        for spider in self.spiders_status:
            spider_text = spider['name']
            status = spider['status']
            btn = SpiderPushButton(spider_text, status)
            btn.delete_signal.connect(self.delete_spider)
            btn.pause_signal.connect(self.pause_spider)
            btn.resume_signal.connect(self.resume_spider)
            self.flow_layout.addWidget(btn)
            self.spider_buttons.append(btn)

    def init_start(self):
        for spider in self.spiders_status:
            spider_text = spider['name']
            status = spider['status']
            if status == "active":
                _main_window = self.window()
                li_str = DatabaseAPI.get_spider_para(spider_text)
                li = eval(li_str)
                li = [str(i) for i in li]
                _main_window.start_add_single_source_process(li, spider_text)
                
    def search_results(self):
        """处理搜索事件"""
        self.spiders_status_total = DatabaseAPI.get_all_spiders_and_status(self.current_page, self.per_page)
        self.spiders_status = self.spiders_status_total['spiders_and_status']
        self.spiders = [spider['name'] for spider in self.spiders_status]
        self.total_items = self.spiders_status_total['total']
        self.total_pages = (self.total_items + self.per_page - 1) // self.per_page
        self.update_page_controls()
        self.spider_buttons.clear()
        self.flow_layout.takeAllWidgets()
        for spider in self.spiders_status:
            spider_text = spider['name']
            status = spider['status']
            btn = SpiderPushButton(spider_text, status)
            btn.delete_signal.connect(self.delete_spider)
            btn.pause_signal.connect(self.pause_spider)
            btn.resume_signal.connect(self.resume_spider)
            self.flow_layout.addWidget(btn)
            self.spider_buttons.append(btn)
    
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
    
    def delete_spider(self, spider_name):
        """删除爬虫"""
        _main_window = self.window()
        msg_box = DeleteConfirmMessageBox("确认删除", "确认删除该爬虫吗？该操作不可撤销。", _main_window)
        msg_box.yesSignal.connect(lambda: self.execute_delete(spider_name))
        msg_box.cancelSignal.connect(lambda: None)
        msg_box.show()
    
    def execute_delete(self, spider_name):
        DatabaseAPI.expire_spider(spider_name)
        _main_window = self.window()
        _main_window.terminate_process(spider_name)
        self.refresh()
        self.createSuccessInfoBar("Expired successfully!")
    
    def pause_spider(self, spider_name):
        """暂停爬虫"""
        DatabaseAPI.pause_spider(spider_name)
        _main_window = self.window()
        _main_window.terminate_process(spider_name)
        self.refresh()
        self.createSuccessInfoBar("Paused successfully!")

    def resume_spider(self, spider_name):
        """恢复爬虫"""
        print(f"resume spider{spider_name}")
        DatabaseAPI.resume_spider(spider_name)
        li_str = DatabaseAPI.get_spider_para(spider_name)
        li = eval(li_str)
        li = [str(i) for i in li]
        _main_window = self.window()
        _main_window.start_add_single_source_process(li, spider_name)
        self.refresh()
        self.createSuccessInfoBar("Resumed successfully!")
    
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
    
    def createSuccessInfoBar(self, content):
        InfoBar.success(
            title='Success',
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000, 
            parent=self
        )
    
    def refresh(self):
        self.search_results()