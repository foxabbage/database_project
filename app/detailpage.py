from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from qfluentwidgets import TabBar, PrimaryPushButton, FluentIcon, ImageLabel, TitleLabel
from .detailtab import DetailTab

class DetailPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabBar = TabBar(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)
        
        # 默认显示的空白页面
        self.defaultPage = QWidget()
        self.setupDefaultPage()
        self.stackedWidget.addWidget(self.defaultPage)
        
        # 连接信号
        main_window = self.window()  # 获取最顶层的窗口
        self.tabBar.tabAddRequested.connect(main_window.switch_to_search)
        self.tabBar.tabCloseRequested.connect(self.closeTab)
        self.tabBar.currentChanged.connect(self.onCurrentChanged)
        
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.tabBar)
        self.vBoxLayout.addWidget(self.stackedWidget)
        
        # 存储标签页信息 {routeKey: widget}
        self.tabs = {}
        
    def setupDefaultPage(self):
        layout = QVBoxLayout(self.defaultPage)
        layout.setAlignment(Qt.AlignCenter)
        
        # 默认图片
        self.defaultLabel = ImageLabel()
        self.defaultLabel.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap("./resources/default_image.jpg")  # 替换为你的图片路径
        if not pixmap.isNull():
            self.defaultLabel.setPixmap(pixmap.scaled(397, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.defaultLabel.setText("默认图片")
        
        # 提示文本
        hintLabel = TitleLabel("没有打开的详情标签页")
        hintLabel.setAlignment(Qt.AlignCenter)
        
        # 添加按钮
        self.addButton = PrimaryPushButton("添加示例标签页", self)
        self.addButton.setIcon(FluentIcon.ADD)
        main_window = self.window()  # 获取最顶层的窗口
        self.addButton.clicked.connect(main_window.switch_to_search)
        
        layout.addWidget(self.defaultLabel)
        layout.addWidget(hintLabel)
        layout.addWidget(self.addButton, 0, Qt.AlignCenter)
    
    def addTab(self, image_id, imgtype=1):
        """添加一个新的DetailTab标签页"""
        routeKey = f"d{imgtype}_{image_id}"
        
        # 如果已经存在该标签页，则切换到它
        if routeKey in self.tabs:
            self.tabBar.setCurrentTab(routeKey)
            self.stackedWidget.setCurrentWidget(self.tabs[routeKey])
            return
            
        # 创建新的DetailTab
        widget = DetailTab(image_id, imgtype)
        widget.setObjectName(routeKey)
        
        # 添加到堆叠窗口
        self.stackedWidget.addWidget(widget)
        self.tabs[routeKey] = widget
        
        # 添加到TabBar
        self.tabBar.addTab(
            routeKey=routeKey,
            text=widget.details['name'],
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )
        
        # 切换到新标签页
        self.tabBar.setCurrentTab(routeKey)
        self.stackedWidget.setCurrentWidget(widget)
        
        # 隐藏默认页面
        self.defaultPage.setVisible(False)
    
    def closeTab(self, index):
        """关闭指定标签页"""
        item = self.tabBar.tabItem(index)
        routeKey = item.routeKey()
        
        if routeKey not in self.tabs:
            return
            
        # 移除widget
        widget = self.tabs[routeKey]
        self.stackedWidget.removeWidget(widget)
        widget.deleteLater()
        
        # 从TabBar移除
        self.tabBar.removeTab(index)
        
        # 从字典移除
        del self.tabs[routeKey]
        
        # 如果没有标签页了，显示默认页面
        if not self.tabs:
            self.defaultPage.setVisible(True)
            self.stackedWidget.setCurrentWidget(self.defaultPage)
    
    def onCurrentChanged(self, routeKey):
        """当前标签页变化时切换页面"""
        if routeKey in self.tabs:
            self.stackedWidget.setCurrentWidget(self.tabs[routeKey])
    
    def currentTab(self):
        """获取当前活动的DetailTab"""
        routeKey = self.tabBar.currentTab()
        return self.tabs.get(routeKey, None)