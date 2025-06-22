from PySide6.QtCore import Qt, QUrl, Signal, QObject, QTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtGui import QPixmap, QPixmapCache
import weakref

class SharedNetworkManager:
    """共享网络管理器单例"""
    _instance = None
    _manager = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._manager = QNetworkAccessManager()
            # 可以在这里设置全局网络配置
        return cls._instance
    
    @property
    def manager(self):
        return self._manager

class ImageLoader(QObject):
    """网络图片加载器（使用共享网络管理器）"""
    loaded = Signal(QPixmap)  # 加载成功信号
    error = Signal(str)       # 加载失败信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用共享的网络管理器
        self.network_manager = SharedNetworkManager().manager
        
        # 设置QPixmapCache缓存大小为100MB (默认是10MB)
        QPixmapCache.setCacheLimit(100 * 1024)  # 参数单位为KB
        
        self.url = ''
        self.current_reply = None
        
        # 超时计时器设置
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._handle_timeout)
        self.timeout_seconds = 10  # 默认10秒超时

    def set_timeout(self, seconds):
        """设置超时时间(秒)"""
        self.timeout_seconds = seconds

    def load(self, url):
        """加载图片（自动处理缓存）"""
        
        # URL标准化处理
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = 'https://' + url
        
        self.url = url
        
        # 取消之前的请求
        if self.current_reply:
            print("[Cancel] 取消之前的请求")
            self.current_reply.abort()
            self.current_reply = None
        
        # 检查缓存
        pixmap = QPixmap()
        if QPixmapCache.find(url, pixmap):
            self.loaded.emit(pixmap)
            return
            
        # 无缓存则发起网络请求
        request = QNetworkRequest(QUrl(url))
        
        # 关键修复1：设置用户代理和接受头
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
        request.setRawHeader(b"Accept", b"image/*")
        
        reply = self.network_manager.get(request)
        self.current_reply = reply
        
        # 添加详细的错误处理
        def on_error(error):
            print(f"[Network] 请求错误: {error} - {reply.errorString()}")
            self.error.emit(reply.errorString())
        
        reply.errorOccurred.connect(on_error)
        
        # 添加SSL错误处理
        def on_ssl_errors(errors):
            print(f"[SSL] SSL错误: {errors}")
            # 可以选择忽略错误（仅用于调试）
            # reply.ignoreSslErrors()
        reply.sslErrors.connect(on_ssl_errors)
        
        # 创建弱引用
        weak_self = weakref.ref(self)
        
        def on_finished():
            # 通过弱引用检查对象是否仍然存在
            self_ref = weak_self()
            if self_ref is None:
                print("[Reference] ImageLoader实例已被销毁，忽略响应")
                reply.deleteLater()
                return
                
            # 处理响应
            self_ref._handle_response(reply)
        
        # 连接完成信号
        reply.finished.connect(on_finished)
        
        # 启动超时计时器
        self.timeout_timer.start(self.timeout_seconds * 1000)
        
    def _handle_response(self, reply):
        """处理网络响应"""
        # 停止超时计时器
        self.timeout_timer.stop()
        
        # 检查是否是当前活动的reply
        if reply != self.current_reply:
            print("[Response] 收到过期回复，忽略处理")
            reply.deleteLater()
            return
            
        # 清除当前reply引用
        self.current_reply = None
        
        if reply.error() != QNetworkReply.NoError:
            if reply.error() != QNetworkReply.OperationCanceledError:  # 忽略手动取消的错误
                error_msg = f"图片加载失败: {reply.errorString()}"
                print(f"[Error] {error_msg}")
                self.error.emit(error_msg)
            else:
                print("[Cancel] 请求已被手动取消")
            reply.deleteLater()
            return
            
        # 读取数据
        data = reply.readAll()
        
        # 加载图片
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            # 存入缓存并发送加载信号
            QPixmapCache.insert(self.url, pixmap)
            self.loaded.emit(pixmap)
        else:
            error_msg = "错误：加载的图片数据无效"
            print(f"[Error] {error_msg}")
            self.error.emit(error_msg)
        
        reply.deleteLater()

    def _handle_timeout(self):
        """处理请求超时"""
        if self.current_reply:
            # 仅取消请求
            self.current_reply.abort()
            self.error.emit(f"错误：图片加载超时({self.timeout_seconds}秒)")
            print("[Timeout] 请求已取消")
