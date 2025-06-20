from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCompleter, QSizePolicy
from PySide6.QtCore import Qt, QStringListModel, QTimer, Signal, QObject
from qfluentwidgets import EditableComboBox, FlowLayout, PillPushButton, StrongBodyLabel, FlyoutView, Flyout, SmoothScrollArea

class TagSignals(QObject):
    tags_changed = Signal(list)

class TagAdder(QWidget):
    def __init__(self, tagsli=[], parent=None):
        super().__init__(parent)
        # 主布局改为竖直布局
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(15)
        
        # 初始化标签数据
        self.all_tags = tagsli
        self.selected_tags = {}  # 改为字典存储，键为tag，值为索引
        self.signals = TagSignals()
        
        # 第一行水平布局（组合框和标题）
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(15)
        
        # 创建组合框
        self.combo = EditableComboBox(self)
        self.combo.setClearButtonEnabled(True)
        self.combo.setPlaceholderText("选择或搜索标签，单击标签删除")
        self.combo.addItems(self.all_tags)
        self.combo.setMaxVisibleItems(8)
        self.combo.setCurrentIndex(-1)
        
        # 设置自动补全
        self.completer_model = QStringListModel(self.all_tags)
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.combo.setCompleter(self.completer)
        
        # 连接信号
        self.combo.activated.connect(self.on_tag_selected)
        self.completer.activated.connect(self.on_comp_tag_selected)
        
        # 创建标签选择器标题
        self.titleLabel = StrongBodyLabel("Tags: ", self)
        self.titleLabel.setAlignment(Qt.AlignCenter)

        # 添加到顶部布局
        self.topLayout.addWidget(self.combo)
        self.topLayout.addWidget(self.titleLabel)
        self.topLayout.setStretch(0, 5)
        self.topLayout.setStretch(1, 1)
        
        # 创建流式布局用于显示已选标签
        self.flowWidget = QWidget()
        self.flowLayout = FlowLayout(self.flowWidget, needAni=False)
        self.flowLayout.setContentsMargins(10, 10, 10, 10)
        self.flowLayout.setHorizontalSpacing(8)
        self.flowLayout.setVerticalSpacing(8)

        # 创建滚动区域
        self.scrollArea = SmoothScrollArea()
        self.scrollArea.setWidgetResizable(True)

        # 设置滚动区域的内容
        self.scrollArea.setWidget(self.flowWidget)
        
        # 添加到主布局
        self.mainLayout.addLayout(self.topLayout)
        self.mainLayout.addWidget(self.scrollArea)
        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 5)

        # 设置尺寸策略和最小尺寸
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumSize(400, 300)  # 设置最小宽度和高度

    def on_tag_selected(self, index):
        """当从组合框的下拉列表中选择标签时调用"""
        if index >= 0:  # 确保是有效的索引
            text = self.combo.itemText(index)
            if text not in self.selected_tags:
                self.add_tag(text)
            elif text in self.selected_tags:
                self.show_flyout()

    def on_comp_tag_selected(self, text):
        """当从自动补全列表中选择标签时调用"""
        if text not in self.selected_tags:
            self.add_tag(text)
        elif text in self.selected_tags:
            self.show_flyout()
    
    def add_tag(self, tag):
        """添加一个新标签"""
        if tag in self.selected_tags:
            return
            
        # 添加按钮到布局
        button = PillPushButton(tag, self.flowWidget)
        button.setCheckable(True)
        button.setChecked(True)
        button.clicked.connect(lambda checked, t=tag: self.on_tag_clicked(checked, t))
        self.flowLayout.addWidget(button)
        
        # 记录当前标签的索引（新添加的在最后）
        self.selected_tags[tag] = self.flowLayout.count() - 1
    
    def on_tag_clicked(self, checked, tag):
        """当标签按钮被点击时调用"""
        if not checked:
            self.remove_tag(tag)
    
    def remove_tag(self, tag):
        """移除一个标签"""
        if tag not in self.selected_tags:
            return
            
        # 获取标签对应的索引
        index = self.selected_tags[tag]
        
        # 使用takeAt移除widget
        widget = self.flowLayout.takeAt(index)
        if widget:
            widget.deleteLater()
        
        # 从字典中移除该标签
        del self.selected_tags[tag]
        
        # 更新其他标签的索引（因为takeAt会影响后面的索引）
        for t, idx in list(self.selected_tags.items()):
            if idx > index:
                self.selected_tags[t] = idx - 1
        
        self.flowLayout.update()

    def show_flyout(self):
        """显示提示信息，表示标签已存在"""
        # 创建FlyoutView的内容
        view = FlyoutView(
            title="",
            content="该标签已存在",
            isClosable=False, 
            parent=self
        )
            
        # 显示Flyout，关联到combo控件
        flyout = Flyout.make(view, self.combo, self)
        flyout.show()
            
        # 自动关闭
        QTimer.singleShot(600, flyout.fadeOut)
