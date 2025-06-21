from PySide6.QtCore import (Qt, Signal, QPropertyAnimation, 
                           QEasingCurve, Property)
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication, QFrame)
from qfluentwidgets import (BodyLabel, ImageLabel, 
                          IndeterminateProgressRing,
                          ElevatedCardWidget, SmoothScrollArea, 
                          RoundMenu, Action, MenuAnimationType, MenuItemDelegate, CheckableMenu, MenuIndicatorType)
from qfluentwidgets import FluentIcon as FIF
from .imageloader import ImageLoader


# 图片卡片组件
class ImageCard(ElevatedCardWidget):
    clicked = Signal(int)  # 点击时发射图片数据
    
    def __init__(self, image_data, img_type=1, parent=None):
        super().__init__(parent)
        self.image_data = image_data
        self.img_type = img_type
        
        #self.setFixedSize(180, 220)
        self.setMinimumWidth(200)
        self.setStyleSheet("""
            #imageCard {
                background: rgba(255, 255, 255, 0.85);  /* 初始半透明白 */
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
                transition: background 200ms ease-out, border 200ms ease-out;  /* 添加CSS过渡 */
            }
            #imageCard:hover {
                background: rgba(220, 220, 220, 0.6);  /* 透明灰 */
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
            
            /* 确保文字清晰 */
            QLabel {
                background: transparent;
                font-family: "Segoe UI", "Microsoft YaHei";
            }
            #titleLabel {
                font-weight: 500;  /* 中等粗细避免模糊 */
            }
        """)
  
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 图片
        self.image_label = ImageLabel(self)
        self.image_label.setFixedSize(160,200)
        self.image_label.setScaledContents(True)
        
        separator = QFrame(self)
        separator.setFrameShape(QFrame.HLine)
        separator.setLineWidth(1)
        separator.setStyleSheet("color: #e0e0e0;")

        # 标题
        self.title_label = BodyLabel(image_data['name'], self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold;font-size: 16px;")
        
        if self.img_type == 2:
            self.type_label = BodyLabel(image_data['source_type'], self)
            self.type_label.setAlignment(Qt.AlignCenter)
            self.type_label.setStyleSheet("color: gray;font-weight: italic;font-size: 12px;")

        # 描述 (截断显示)
        desc = image_data['description']
        if desc is None:
            desc = ""
        if len(desc) > 30:
            desc = desc[:30] + "..."
        self.desc_label = BodyLabel(desc, self)
        self.desc_label.setStyleSheet("font-size: 10px;")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(40)
        
        # 加载指示器
        self.loading_indicator = IndeterminateProgressRing(self.image_label)
        self.loading_indicator.setFixedSize(40, 40)
        
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.loading_indicator, 0, Qt.AlignCenter)
        layout.addWidget(separator)
        layout.addWidget(self.title_label)
        if self.img_type == 2:
            layout.addWidget(self.type_label)
        layout.addWidget(self.desc_label)
        layout.addStretch(1)

        self.init_loader()
    
    def init_loader(self):
        """初始化图片加载器"""
        if self.image_data['is_downloaded']:
            self.loading_indicator.hide()
            self.image_label.setPixmap(self.image_data['local_path'])
        else:
            self.loader = ImageLoader(self)
            self.loader.loaded.connect(self.on_image_loaded)
            self.loader.error.connect(self.on_load_error)
            self.loader.load(self.image_data['url'])
        
    def on_image_loaded(self, pixmap):
        """图片加载完成处理"""
        self.loading_indicator.hide()
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setImage(scaled)
        
    def on_load_error(self, error_msg):
        """图片加载失败处理"""
        self.loading_indicator.hide()
        self.image_label.setText("加载失败")
        print(error_msg)
        
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_data['id'])
        else:
            self.contextMenuEvent(event)

    def mouseReleaseEvent(self, e):
        '''覆盖鼠标释放事件，防止报错'''
        pass

    def contextMenuEvent(self, e):
        menu = RoundMenu(parent=self)
        
        # 创建Copy主菜单项及其子菜单
        copy_menu = RoundMenu("Copy", self)
        copy_menu.setIcon(FIF.COPY)
        copy_menu.addActions([
            Action(FIF.PHOTO, 'Copy picture', triggered=lambda: self.copy_to_clipboard("picture")),
            Action(FIF.TAG, 'Copy name', triggered=lambda: self.copy_to_clipboard("name")),
            Action(FIF.DOCUMENT, 'Copy description', triggered=lambda: self.copy_to_clipboard("description")),
        ])
        menu.addMenu(copy_menu)

        # 显示菜单
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def copy_to_clipboard(self, data_type):
        """将指定类型的数据复制到剪贴板"""
        clipboard = QApplication.clipboard()
        
        if data_type == "picture":
            clipboard.setPixmap(self.image_label.pixmap())
        elif data_type == "name":
            clipboard.setText(self.image_data['name'])
        elif data_type == "description":
            clipboard.setText(self.image_data['description'])
