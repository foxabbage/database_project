from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QThread
from qfluentwidgets import (LineEdit, ComboBox, CheckBox, PushButton, 
                           BodyLabel, SpinBox, DoubleSpinBox,  InfoBar, InfoBarPosition, 
                           FastCalendarPicker, PrimaryPushButton, MessageBoxBase)
from .process_spider_dict import process_spider_config
from .bangumirequest import bangumi_request, bangumi_request_all
from .multiselect import MultiSelectWidget
from .databaseapi import DatabaseAPI
from .deletemessagebox import ProcessingMessageBox
import re

class MultiSelectMessageBox(MessageBoxBase):
    """标签添加对话框"""
    yesSignal = Signal(list)
    cancelSignal = Signal()
    def __init__(self, name_id: dict, total,  parent=None):
        super().__init__(parent)
        self.name_id = name_id
        nameli = name_id.keys()
        self.textselecter = MultiSelectWidget(nameli, total)
        self.viewLayout.addWidget(self.textselecter)
        # 隐藏按钮
        self.cancelButton.setText('取消')
        self.yesButton.setText('确定')
        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)
        
        # 设置对话框样式
        self.widget.setMinimumWidth(550)
    
    def __onYesButtonClicked(self):
        selected = [
            widget.checkbox.text() 
            for widget in self.textselecter.item_widgets 
            if widget.checkbox.isChecked()
        ]
        selected = [self.name_id[name] for name in selected]
        self.accept()
        self.yesSignal.emit(selected)
    
    def __onCancelButtonClicked(self):
        self.reject()
        self.cancelSignal.emit()

class SearchThread(QThread):
    finished = Signal(dict, int)  # 传递 name_id 和 total_fact
    
    def __init__(self, search_payload, data):
        super().__init__()
        self.search_payload = search_payload
        self.data = data
    
    def run(self):
        total, name_id = bangumi_request(self.search_payload, 0)
        total_fact = min(total, self.data["limit"])
        name_id = bangumi_request_all(self.search_payload, total_fact)
        self.finished.emit(name_id, total_fact)


class SpiderConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        
        # 爬虫名字
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("请输入爬虫名称")
        layout.addWidget(BodyLabel("爬虫名字："))
        layout.addWidget(self.name_edit)
        
        # 关键词
        self.keyword_edit = LineEdit()
        self.keyword_edit.setPlaceholderText("请输入关键词")
        layout.addWidget(BodyLabel("关键词："))
        layout.addWidget(self.keyword_edit)
        
        # 排序方式和是否下载图片到本地放在同一行
        sort_download_layout = QHBoxLayout()
        
        # 排序方式
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(BodyLabel("排序方式："))
        self.sort_combo = ComboBox()
        self.sort_combo.addItems(["排名", "收藏数", "评分", "匹配程度"])
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        sort_download_layout.addLayout(sort_layout)
        
        layout.addLayout(sort_download_layout)
        
        """
        # 类型（多选）
        layout.addWidget(BodyLabel("类型："))
        self.type_layout = QHBoxLayout()
        self.book_check = CheckBox("书籍")
        self.anime_check = CheckBox("动画")
        self.game_check = CheckBox("游戏")
        self.book_check.setChecked(True)
        self.anime_check.setChecked(True)
        self.game_check.setChecked(True)
        self.type_layout.addWidget(self.book_check)
        self.type_layout.addWidget(self.anime_check)
        self.type_layout.addWidget(self.game_check)
        self.type_layout.addStretch()
        layout.addLayout(self.type_layout)"""
        
        # 标签
        self.tag_edit = LineEdit()
        self.tag_edit.setPlaceholderText("不同标签通过逗号隔开")
        layout.addWidget(BodyLabel("标签："))
        layout.addWidget(self.tag_edit)
        
        # 时间范围
        layout.addWidget(BodyLabel("时间范围："))
        self.time_layout = QHBoxLayout()
        self.start_date_picker = FastCalendarPicker()
        self.end_date_picker = FastCalendarPicker()
        self.time_layout.addWidget(self.start_date_picker)
        self.time_layout.addWidget(BodyLabel("到"))
        self.time_layout.addWidget(self.end_date_picker)
        self.time_layout.addStretch()
        layout.addLayout(self.time_layout)
        
        # 评分范围
        layout.addWidget(BodyLabel("评分范围："))
        self.rating_layout = QHBoxLayout()
        self.min_rating_spin = DoubleSpinBox()
        self.min_rating_spin.setRange(0, 10)
        self.max_rating_spin = DoubleSpinBox()
        self.max_rating_spin.setRange(0, 10)
        self.max_rating_spin.setValue(10)
        self.rating_layout.addWidget(self.min_rating_spin)
        self.rating_layout.addWidget(BodyLabel("到"))
        self.rating_layout.addWidget(self.max_rating_spin)
        self.rating_layout.addStretch()
        layout.addLayout(self.rating_layout)
        
        # 排名范围
        layout.addWidget(BodyLabel("排名范围："))
        self.rank_layout = QHBoxLayout()
        self.min_rank_spin = SpinBox()
        self.min_rank_spin.setRange(1, 99999)
        self.max_rank_spin = SpinBox()
        self.max_rank_spin.setRange(1, 99999)
        self.max_rank_spin.setValue(1000)
        self.rank_layout.addWidget(self.min_rank_spin)
        self.rank_layout.addWidget(BodyLabel("到"))
        self.rank_layout.addWidget(self.max_rank_spin)
        self.rank_layout.addStretch()
        layout.addLayout(self.rank_layout)
        
        # 条目上限
        self.limit_spin = SpinBox()
        self.limit_spin.setRange(1, 200)
        self.limit_spin.setValue(60)
        layout.addWidget(BodyLabel("条目上限："))
        layout.addWidget(self.limit_spin)
        
        # 确认按钮
        self.confirm_btn = PrimaryPushButton("确认")
        self.confirm_btn.clicked.connect(self.on_confirm)
        
        # 将按钮放在布局中央
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 调整布局间距
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
    
    def on_confirm(self):
        """收集所有数据并传递给处理函数"""
        if self.name_edit.text() == "":
            self.createErrorInfoBar()
            return
        self.name = self.name_edit.text()
        self.download_to_local = False
        tags_tmp = re.split(r'[,，]', self.tag_edit.text())
        tags=[]
        for tag in tags_tmp:
            if tag != '':
                tags.append(tag)
        if len(tags) == 0:
            tags = None
        data = {
            "keyword": self.keyword_edit.text(),
            "sort": self.sort_combo.currentText(),
            "types": self.get_selected_types(),
            "tags": tags,
            "start_date": self.start_date_picker.getDate().toString(Qt.ISODate),
            "end_date": self.end_date_picker.getDate().toString(Qt.ISODate),
            "min_rating": self.min_rating_spin.value(),
            "max_rating": self.max_rating_spin.value(),
            "min_rank": self.min_rank_spin.value(),
            "max_rank": self.max_rank_spin.value(),
            "limit": self.limit_spin.value()
        }
        
        self.data = data
        # 调用数据处理函数
        _main_window = self.window()
        self.load_dia = ProcessingMessageBox("正在加载中", "请求速度较慢，请耐心等待", _main_window)
        self.load_dia.show()
        QApplication.processEvents()
    
        # 创建并启动工作线程
        self.search_payload = process_spider_config(self.data)
        self.search_thread = SearchThread(self.search_payload, self.data)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.start()

    
    def on_search_finished(self, name_id, total_fact):
        # 关闭加载对话框
        self.load_dia.accept()
        
        # 显示选择对话框
        _main_window = self.window()
        self.text_select = MultiSelectMessageBox(name_id, total_fact, _main_window)
        self.text_select.yesSignal.connect(self.add_spider)
        self.text_select.cancelSignal.connect(lambda: None)
        self.text_select.show()
    
    def get_selected_types(self):
        """获取选中的类型"""
        types = ["动画"]
        """
        if self.book_check.isChecked():
            types.append("书籍")
        if self.anime_check.isChecked():
            types.append("动画")
        if self.game_check.isChecked():
            types.append("游戏")"""
        return types
    
    def createErrorInfoBar(self):
        InfoBar.error(
            title='Error',
            content="Name is required!",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000, 
            parent=self
        )
    
    def createSuccessInfoBar(self):
        InfoBar.success(
            title='Success',
            content="Added successfully!",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000, 
            parent=self
        )
    
    def createErrorInfoBar0(self):
        InfoBar.error(
            title='Error',
            content="No items selected!",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000, 
            parent=self
        )
    
    def add_spider(self, idlist):
        if len(idlist) == 0:
            self.createErrorInfoBar0()
            return
        DatabaseAPI.add_spider(self.name, str(idlist), self.download_to_local)
        self.createSuccessInfoBar()
        _main_window = self.window()
        idlist = [str(i) for i in idlist]
        _main_window.start_add_single_source_process(idlist, self.name)
        _main_window.refresh_setting_page()

    def refresh(self):
        self.name_edit.clear()
        self.keyword_edit.clear()
        self.sort_combo.setCurrentIndex(0)
        self.tag_edit.clear()
        self.start_date_picker.reset()
        self.end_date_picker.reset()
        self.min_rating_spin.setValue(0)
        self.max_rating_spin.setValue(10)
        self.min_rank_spin.setValue(0)
        self.max_rank_spin.setValue(1000)
        self.limit_spin.setValue(60)
        #self.book_check.setChecked(True)
        #self.anime_check.setChecked(True)
        #self.game_check.setChecked(True)
