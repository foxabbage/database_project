from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout, QSizePolicy, QSpacerItem
from qfluentwidgets import SegmentedWidget, TransparentToolButton
from qfluentwidgets import FluentIcon as FIF
from .subsearchpage import SubSearchPage

class SearchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SearchPage")
        
        # 主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(20, 10, 20, 0)
        self.vBoxLayout.setSpacing(0)
        
        # 创建分段导航栏和堆叠窗口
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        
        # 创建两个搜索页面
        self.page_role = SubSearchPage(1)
        self.page_source = SubSearchPage(2)

        self.sync_button = TransparentToolButton(FIF.SYNC, self)
        self.sync_button.setToolTip('refresh')
        self.sync_button.clicked.connect(self.refresh_by_index)
        
        # 添加子界面
        self.addSubInterface(self.page_role, 'page_role', '角色')
        self.addSubInterface(self.page_source, 'page_source', '作品')
        
        # 添加到布局
        h_layout = QHBoxLayout()
        right_stretch = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_layout.addWidget(self.pivot)
        h_layout.addItem(right_stretch)
        h_layout.addWidget(self.sync_button)
        h_layout.setStretch(0, 2)
        h_layout.setStretch(1, 7)
        h_layout.setStretch(2, 1)
        
        self.vBoxLayout.addLayout(h_layout)
        self.vBoxLayout.addWidget(self.stackedWidget)
        
        # 设置初始页面
        self.stackedWidget.setCurrentWidget(self.page_role)
        self.pivot.setCurrentItem('page_role')
        
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
        if self.page_role.current_name != '' or len(self.page_role.current_tags) != 0 or self.page_role.total_items != 0:
            self.page_role.do_search()
        if self.page_source.current_name != '' or len(self.page_source.current_tags) != 0 or self.page_source.total_items != 0:
            self.page_source.do_search()
    
    def refresh_by_index(self):
        if self.pivot.currentRouteKey() == 'page_role':
            if self.page_role.current_name != '' or len(self.page_role.current_tags) != 0 or self.page_role.total_items != 0:
                self.page_role.search_results()
        else:
            if self.page_source.current_name != '' or len(self.page_source.current_tags) != 0 or self.page_source.total_items != 0:
                self.page_source.search_results()
    
    def clear(self):
        self.page_role.search_results(clear=True)
        self.page_source.search_results(clear=True)
