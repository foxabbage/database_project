from PySide6.QtCore import Signal
from qfluentwidgets import (BodyLabel, TitleLabel, IconWidget, MessageBoxBase,  
                           IndeterminateProgressBar, TitleLabel, BodyLabel)
from qfluentwidgets import FluentIcon as FIF

class DeleteConfirmMessageBox(MessageBoxBase):
    """删除确认对话框"""
    yesSignal = Signal()
    cancelSignal = Signal()

    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.titleLabel = TitleLabel(title, self)
        self.contentLabel = BodyLabel(content, self)
        
        # 添加控件到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        
        # 设置按钮文本
        self.yesButton.setText('确认删除')
        self.cancelButton.setText('取消')
        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)
        
        # 设置对话框样式
        self.widget.setMinimumWidth(350)

    def __onCancelButtonClicked(self):
        self.reject()
        self.cancelSignal.emit()

    def __onYesButtonClicked(self):
        self.accept()
        self.yesSignal.emit()

class ProcessingMessageBox(MessageBoxBase):
    """处理中对话框"""
    
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.titleLabel = TitleLabel(title, self)
        self.contentLabel = BodyLabel(content, self)
        self.progressBar = IndeterminateProgressBar(self)
        
        # 添加控件到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        self.viewLayout.addWidget(self.progressBar)
        
        # 隐藏按钮
        self.hideYesButton()
        self.hideCancelButton()
        
        # 设置对话框样式
        self.widget.setMinimumWidth(350)

class DeleteResultMessageBox(MessageBoxBase):
    """删除成功对话框"""
    yesSignal = Signal()
    
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.titleLabel = TitleLabel(title, self)
        self.contentLabel = BodyLabel(content, self)
        self.icon = IconWidget(FIF.COMPLETED, self)
        self.icon.setFixedSize(60, 60)
        
        # 添加控件到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        self.viewLayout.addWidget(self.icon)
        
        # 设置按钮文本
        self.yesButton.setText('确定')
        self.hideCancelButton()
        
        # 设置对话框样式
        self.widget.setMinimumWidth(350)
        self.yesButton.clicked.connect(self.__onYesButtonClicked)

    def __onYesButtonClicked(self):
        self.accept()
        self.yesSignal.emit()

class DeleteResultMessageBoxError(MessageBoxBase):
    """删除成功对话框"""
    yesSignal = Signal()
    
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.titleLabel = TitleLabel(title, self)
        self.contentLabel = BodyLabel(content, self)
        self.icon = IconWidget(FIF.CANCEL_MEDIUM, self)
        self.icon.setFixedSize(60, 60)
        
        # 添加控件到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        self.viewLayout.addWidget(self.icon)
        
        # 设置按钮文本
        self.yesButton.setText('确定')
        self.hideCancelButton()
        
        # 设置对话框样式
        self.widget.setMinimumWidth(350)
        self.yesButton.clicked.connect(self.__onYesButtonClicked)

    def __onYesButtonClicked(self):
        self.accept()
        self.yesSignal.emit()