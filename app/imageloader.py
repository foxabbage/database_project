from PySide6.QtCore import Qt, QUrl, Signal, QObject, QTimer
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
        self.url = ''
        self.current_reply = None
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._handle_timeout)
        self.timeout_seconds = 10  # 默认10秒超时

    def set_timeout(self, seconds):
        """设置超时时间(秒)"""
        self.timeout_seconds = seconds

    def load(self, url):
        """加载图片（自动处理缓存）"""
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = 'https://' + url
        
        self.url = url
        
        # 取消之前的请求
        if self.current_reply:
            self.current_reply.abort()
            self.current_reply.deleteLater()
            self.current_reply = None
        
        # 先检查缓存
        pixmap = QPixmap()
        if QPixmapCache.find(url, pixmap):
            self.loaded.emit(pixmap)
            return
            
        # 无缓存则发起网络请求
        request = QNetworkRequest(QUrl(url))
        self.current_reply = self.network_manager.get(request)
        # 使用 lambda 正确处理参数
        self.current_reply.finished.connect(lambda: self._handle_response(self.current_reply))
        
        # 启动超时计时器
        self.timeout_timer.start(self.timeout_seconds * 1000)
        
    def _handle_response(self, reply):
        """处理网络响应"""
        # 停止超时计时器
        self.timeout_timer.stop()
        
        # 检查是否是当前活动的reply
        if reply != self.current_reply:
            reply.deleteLater()
            return
            
        if reply.error() != QNetworkReply.NoError:
            if reply.error() != QNetworkReply.OperationCanceledError:  # 忽略手动取消的错误
                error_msg = f"图片加载失败: {reply.errorString()}"
                self.error.emit(error_msg)
            reply.deleteLater()
            self.current_reply = None
            return
            
        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        reply.deleteLater()
        self.current_reply = None
        
        if not pixmap.isNull():
            # 存入缓存并发送加载信号
            QPixmapCache.insert(self.url, pixmap)
            self.loaded.emit(pixmap)
        else:
            self.error.emit("错误：加载的图片数据无效")

    def _handle_timeout(self):
        """处理请求超时"""
        if self.current_reply:
            self.current_reply.abort()
            self.current_reply.deleteLater()
            self.current_reply = None
            self.error.emit(f"错误：图片加载超时({self.timeout_seconds}秒)")

    def cancel(self):
        """取消当前加载"""
        if self.current_reply:
            self.timeout_timer.stop()
            self.current_reply.abort()
            self.current_reply.deleteLater()
            self.current_reply = None