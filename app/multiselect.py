from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import SmoothScrollArea, CheckBox, PushButton, ScrollArea, BodyLabel


class SelectableItemWidget(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.checkbox = CheckBox(text)
        self.checkbox.setChecked(True)
        self.layout.addWidget(self.checkbox)
        self.layout.addStretch()
        self.setLayout(self.layout)


class MultiSelectWidget(QWidget):
    selection_changed = Signal(list)

    def __init__(self, items: list[str], total=0, parent=None):
        super().__init__(parent)
        self.items = items
        self.total = total
        self.item_widgets = []
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        self.total_label = BodyLabel(f"共 {self.total} 项")
        self.layout.addWidget(self.total_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        # 全选按钮
        self.select_all_button = CheckBox("全选")
        self.select_all_button.setChecked(True)
        self.select_all_button.stateChanged.connect(self.on_select_all_changed)
        self.layout.addWidget(self.select_all_button)

        # 可滚动区域
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # 创建可选项
        for item in self.items:
            widget = SelectableItemWidget(item)
            widget.checkbox.stateChanged.connect(self.on_item_changed)
            self.scroll_layout.addWidget(widget)
            self.item_widgets.append(widget)

        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        self.setLayout(self.layout)

    def on_select_all_changed(self, state):
        # 只有当全选按钮状态变化时才影响所有选项
        # 这里需要暂时断开信号连接，避免触发item_changed
        for widget in self.item_widgets:
            widget.checkbox.stateChanged.disconnect(self.on_item_changed)
            widget.checkbox.setChecked(state)
            widget.checkbox.stateChanged.connect(self.on_item_changed)

    def on_item_changed(self):
        # 当单个选项变化时，更新全选按钮状态
        all_checked = all(widget.checkbox.isChecked() for widget in self.item_widgets)
        
        # 同样需要暂时断开信号连接，避免循环触发
        self.select_all_button.stateChanged.disconnect(self.on_select_all_changed)
        self.select_all_button.setChecked(all_checked)
        self.select_all_button.stateChanged.connect(self.on_select_all_changed)
