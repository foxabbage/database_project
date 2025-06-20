from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout, QSizePolicy, QSpacerItem
from PySide6.QtCore import Qt
from qfluentwidgets import SegmentedWidget, TransparentToolButton
from qfluentwidgets import FluentIcon as FIF, InfoBar, InfoBarPosition, ProgressBar
from .allspider import SubSpiderPage
from .addspider import SpiderConfigWidget

class SettingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SettingPage")
        
        # 主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(20, 10, 20, 0)
        self.vBoxLayout.setSpacing(0)
        
        # 创建分段导航栏和堆叠窗口
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        
        # 创建两个搜索页面
        self.all_spider = SubSpiderPage(self)
        self.add_spider = SpiderConfigWidget(self)
        
        # 添加子界面
        self.addSubInterface(self.all_spider, 'all_spider', '所有爬虫')
        self.addSubInterface(self.add_spider, 'add_spider', '添加爬虫')
        
        # 添加到布局
        h_layout = QHBoxLayout()
        right_stretch = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_layout.addWidget(self.pivot)
        h_layout.addItem(right_stretch)
        h_layout.setStretch(0, 2)
        h_layout.setStretch(1, 8)
        
        self.vBoxLayout.addLayout(h_layout)
        self.vBoxLayout.addWidget(self.stackedWidget)
        
        # 设置初始页面
        self.stackedWidget.setCurrentWidget(self.all_spider)
        self.pivot.setCurrentItem('all_spider')
        
        # 连接信号槽
        self.pivot.currentItemChanged.connect(self.onCurrentChanged)
    
    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        """添加子界面到堆叠窗口和导航栏"""
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)
    
    def onCurrentChanged(self, routeKey: str):
        """导航栏切换时的槽函数"""
        widget = self.findChild(QWidget, routeKey)
        if widget:
            self.stackedWidget.setCurrentWidget(widget)
    
    def refresh(self):
        self.all_spider.refresh()
        self.add_spider.refresh()
    
    def add_import_task(self, name):
        """添加新导入任务到UI"""
        InfoBar.success(
            title='任务已添加',
            content=f'爬虫任务 "{name}" 已添加到队列',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        self._progress_infobar = InfoBar.info(
            title='任务进行中',
            content=f'正在执行爬虫任务 "{name}"...',
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,  # 永久显示
            parent=self
        )
        # 如果需要实际添加到UI列表，可以在这里添加代码
        
    def remove_import_task(self, name):
        """从UI移除导入任务"""
        self._progress_infobar.close()
        InfoBar.warning(
            title='任务已移除',
            content=f'爬虫任务 "{name}" 已从队列移除',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        # 如果需要实际从UI列表移除，可以在这里添加代码
        
    def complete_import_task(self, name):
        """标记任务为已完成"""
        self._progress_infobar.close()
        InfoBar.success(
            title='任务完成',
            content=f'爬虫任务 "{name}" 已完成',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        # 如果需要更新UI中的任务状态，可以在这里添加代码
