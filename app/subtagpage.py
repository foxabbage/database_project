from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QApplication
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from qfluentwidgets import (SmoothScrollArea, FlowLayout, PushButton, SearchLineEdit, PrimaryToolButton,
                            PushButton, LineEdit, BodyLabel, InfoBar, InfoBarPosition, MessageBoxBase, 
                            RoundMenu, Action, MenuAnimationType)
from .databaseapi import DatabaseAPI
from qfluentwidgets import FluentIcon as FIF
from .deletemessagebox import *
import re

class NewTagMessageBox(MessageBoxBase):
    """标签添加对话框"""
    yesSignal = Signal(str)
    cancelSignal = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tagadder = LineEdit(self)
        self.tagadder.setPlaceholderText("输入一个标签")
        self.tagadder.setFixedWidth(350)
        self.tagadder.setFixedHeight(40)
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
        self.yesSignal.emit(self.tagadder.text())
    
    def __onCancelButtonClicked(self):
        self.reject()
        self.cancelSignal.emit()

class TagPushButton(PushButton):
    """标签按钮"""
    delete_signal = Signal(str)
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setText(text)
    
    def mousePressEvent(self, event):
        self.contextMenuEvent(event)
    
    def contextMenuEvent(self, e):
        menu = RoundMenu(parent=self)
        
        # 创建Copy主菜单项及其子菜单
        menu.addAction(Action(FIF.COPY, 'Copy', triggered = self.copy_to_clipboard))
        menu.addAction(Action(FIF.CLOSE, 'Delete', triggered = self.on_delete))
        menu.actions()[0].setCheckable(True)
        menu.actions()[0].setChecked(True)

        # 显示菜单
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def copy_to_clipboard(self):
        """将指定类型的数据复制到剪贴板"""
        clipboard = QApplication.clipboard()
        match = re.match(r'^(.*?)\|', self.text)
        clipboard.setText(match.group(1).strip())
    
    def on_delete(self):
        self.delete_signal.emit(self.text)

class SubTagPage(QWidget):
    def __init__(self, imgtype, parent=None):
        super().__init__(parent)
        self.setObjectName("SubTagPage")
        self.imgtype = imgtype
        self.per_page = 60
        self.tags_num_total = DatabaseAPI.get_all_tags_and_num(self.imgtype, 1, self.per_page)
        self.total_items = self.tags_num_total['total']
        self.tags_num = self.tags_num_total['tags_and_nums']
        self.tags = [tags['tag'] for tags in self.tags_num]
        self.current_text = ""
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 15, 0, 20)
        self.main_layout.setSpacing(10)
        
        self.addbutton = PrimaryToolButton(FIF.ADD, self)
        self.addbutton.setToolTip("添加标签")
        self.addbutton.clicked.connect(self.show_new_tag_dialog)
        self.h_widget = QWidget()
        self.h_layout = QHBoxLayout(self.h_widget)

        # 搜索栏
        self.search_box = SearchLineEdit(self)
        self.search_box.setPlaceholderText("输入名字搜索")
        self.search_box.setFixedWidth(400)
        self.search_box.searchButton.clicked.connect(self.do_search)
        self.search_box.returnPressed.connect(self.do_search)
        self.h_layout.addWidget(self.search_box, alignment=Qt.AlignLeft)
        self.h_layout.addWidget(self.addbutton, alignment=Qt.AlignRight)
        self.main_layout.addWidget(self.h_widget)
        
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
        
        self.tag_buttons = []
        for tag in self.tags_num:
            tag_text = tag['tag']
            n = tag['num']
            text = f'{tag_text} | {n}'
            btn = TagPushButton(text)
            btn.delete_signal.connect(self.delete_tag)
            self.flow_layout.addWidget(btn)
            self.tag_buttons.append(btn)
    
    def do_search(self):
        self.current_text = self.search_box.text()
        self.current_page = 1
        self.search_results()

    def search_results(self):
        """处理搜索事件"""
        if self.current_text != "":
            self.tags_num_total = DatabaseAPI.get_all_tags_and_num_by_name(self.imgtype, self.current_text, self.current_page, self.per_page)
        else:
            self.tags_num_total = DatabaseAPI.get_all_tags_and_num(self.imgtype, self.current_page, self.per_page)
        self.tags_num = self.tags_num_total['tags_and_nums']
        self.tags = [tags['tag'] for tags in self.tags_num]
        self.total_items = self.tags_num_total['total']
        self.total_pages = (self.total_items + self.per_page - 1) // self.per_page
        self.update_page_controls()
        self.tag_buttons.clear()
        self.flow_layout.takeAllWidgets()
        for tag in self.tags_num:
            tag_text = tag['tag']
            n = tag['num']
            text = f'{tag_text} | {n}'
            btn = TagPushButton(text)
            btn.delete_signal.connect(self.delete_tag)
            self.flow_layout.addWidget(btn)
            self.tag_buttons.append(btn)
    
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

    def show_new_tag_dialog(self):
        _main_window = self.window()
        self.tag_adder_widget = NewTagMessageBox(_main_window)
        self.tag_adder_widget.yesSignal.connect(self.add_tag)
        self.tag_adder_widget.cancelSignal.connect(lambda: None)
        self.tag_adder_widget.show()

    def add_tag(self, tag_text):
        if tag_text == "":
            return
        tag_exist = DatabaseAPI.check_tag_exist(self.imgtype, tag_text)
        if tag_exist:
            self.createTagExistInfoBar()
        else:
            DatabaseAPI.add_tag(self.imgtype, tag_text)
            self.createAddTagSuccessInfoBar()
            self.do_search()
    
    def createTagExistInfoBar(self):
        InfoBar.error(
            title='Error',
            content="Tag already exists",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,  
            parent=self
        )
    
    def createAddTagSuccessInfoBar(self):
        InfoBar.success(
            title='Success',
            content="Tag added successfully",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,  
            parent=self
        )

    def delete_tag(self, tag_text):
        title = "确认删除"
        content = f"确定要删除这个标签吗？此操作不可撤销！"
        _main_window = self.window()
        self.tag_deleter_widget = DeleteConfirmMessageBox(title, content, _main_window)
        self.tag_deleter_widget.yesSignal.connect(lambda: self.execute_delete(tag_text))
        self.tag_deleter_widget.cancelSignal.connect(lambda: None)
        self.tag_deleter_widget.show()
    
    def execute_delete(self, tag_text):
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
        match = re.match(r'^(.*?)\|', tag_text)
        deletebool = DatabaseAPI.delete_tag(self.imgtype, match.group(1).strip())
        if deletebool:
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
            _main_window = self.window()
            DeleteResultMessageBoxError(
                "删除失败", 
                f"删除过程中发生错误", 
                _main_window
            ).show()

    def close_tab(self):
        """Close this tab by calling parent's close_tab method"""
        _main_window = self.window()
        self.do_search()
        _main_window.clear_refresh()

