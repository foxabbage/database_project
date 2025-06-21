from PySide6.QtCore import Qt, QUrl, Signal, QObject
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtGui import QPixmap, QPixmapCache

class ImageLoader(QObject):
    """网络图片加载器"""
    loaded = Signal(QPixmap)  # 加载成功信号
    error = Signal(str)       # 加载失败信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager(self)
        # 设置QPixmapCache缓存大小为100MB (默认是10MB)
        QPixmapCache.setCacheLimit(100 * 1024)  # 参数单位为KB
        self.url=''

    def load(self, url):
        """加载图片（自动处理缓存）"""
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = 'https://' + url
        
        self.url=url
        # 先检查缓存
        pixmap = QPixmap()
        if QPixmapCache.find(url, pixmap):
            self.loaded.emit(pixmap)
            return
            
        # 无缓存则发起网络请求
        request = QNetworkRequest(QUrl(url))
        self.network_manager.finished.connect(self._handle_response)
        self.network_manager.get(request)

    def _handle_response(self, reply):
        """处理网络响应"""
        if reply.error()!= QNetworkReply.NoError:
            error_msg = f"图片加载失败: {reply.errorString()}"
            self.error.emit(error_msg)
            reply.deleteLater()
            return
            
        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        reply.deleteLater()
        
        if not pixmap.isNull():
            # 存入缓存并发送加载信号
            QPixmapCache.insert(self.url, pixmap)
            self.loaded.emit(pixmap)
        else:
            self.error.emit("错误：加载的图片数据无效")
