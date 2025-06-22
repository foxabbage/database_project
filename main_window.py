import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QObject, QThread
from PySide6.QtGui import QPixmap, QIntValidator, QIcon
from qfluentwidgets import (NavigationInterface, NavigationItemPosition, FluentWindow, 
                           SearchLineEdit, PushButton, MessageBox, 
                           setTheme, Theme, SmoothScrollArea, SplashScreen)
from qfluentwidgets import FluentIcon as FIF
from init import load_db_config
DB_CONFIG = load_db_config()
DB_CONFIG['database'] = 'anime'
from app.databaseapi import DatabaseAPI
DatabaseAPI.initialize(f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@localhost/anime")
from app.detailpage import DetailPage
from app.searchpage import SearchPage
from app.tagpage import TagPage
from app.settingpage import SettingPage
from kirakiradokidoki.add_single_source import add_single_source
import re


class AddSourceWorker(QObject):
    finished = Signal(str)  # 传递线程名称
    progress = Signal(int, str)  # 进度值和线程名称
    error = Signal(str, str)  # 错误信息和线程名称

    def __init__(self, li, thread_name):
        super().__init__()
        self.li = li
        self.thread_name = thread_name
        self._is_running = True

    def run(self):
        try:
            if not self._is_running:
                return
                
            result = add_single_source(self.li, DB_CONFIG)
            
            if not self._is_running:
                return
                
            if result is not None and "error" in result:
                self.error.emit(result["error"], self.thread_name)
            else:
                self.progress.emit(100, self.thread_name)
                
        except Exception as e:
            self.error.emit(str(e), self.thread_name)
        finally:
            self.finished.emit(self.thread_name)

    def stop(self):
        self._is_running = False
# 所有的区分角色和来源的type均以角色为1，来源为2
# 主窗口
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        setTheme(Theme.AUTO)
        self.setFixedSize(1280, 800)
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowIcon(QIcon('./resources/icon.jpg'))
        self.setWindowTitle('KiraKira DokiDoki!!')

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(300, 300))
        self.splashScreen.raise_()
        self.splashScreen.show()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()
        
        # 初始化
        self.active_workers = {}
        DatabaseAPI.delete_extired_spider()
        
        # 创建页面
        self.search_page = SearchPage(self)
        self.detail_page = DetailPage(self)
        self.tag_page = TagPage(self)
        self.setting_page = SettingPage(self)
        self.search_page.setObjectName("searchPage")
        self.detail_page.setObjectName("detailPage")
        self.tag_page.setObjectName("tagPage")
        self.setting_page.setObjectName("settingPage")
        
        # 添加导航项
        self.addSubInterface(interface = self.search_page, icon=FIF.SEARCH, text = "search")
        self.addSubInterface(interface = self.detail_page, icon=FIF.PHOTO, text = "detail")
        self.addSubInterface(interface = self.tag_page, icon=FIF.TAG, text = "tag")
        self.addSubInterface(interface = self.setting_page, icon=FIF.SETTING, text = "setting", position=NavigationItemPosition.BOTTOM)
        
        # 默认显示搜索页
        self.splashScreen.finish()
        self.navigationInterface.setCurrentItem("search")
        self.setting_page.all_spider.init_start()
        
    def show_image_detail_role(self, image_id):
        """显示图片详情页"""
        self.detail_page.addTab(image_id, 1)
        self.switchTo(self.detail_page)
    
    def show_image_detail_source(self, image_id):
        """显示图片详情页"""
        self.detail_page.addTab(image_id, 2)
        self.switchTo(self.detail_page)
        
    def switch_to_search(self):
        """切换回搜索页"""
        self.switchTo(self.search_page)
        self.navigationInterface.setCurrentItem("search")
    
    def refresh(self):
        """刷新页面"""
        self.search_page.refresh()
        routekeys = self.detail_page.tabs
        rli = list(routekeys)
        for key in rli:
            pattern = r"d(\d+)_(\d+)"
            match = re.match(pattern, key)
            imgtype = int(match.group(1))  # 第一个括号匹配的内容
            image_id = int(match.group(2))  # 第二个括号匹配的内容
            self.detail_page.closeTab(self.detail_page.tabBar.items.index(self.detail_page.tabBar.tab(key)))
            test_exist = DatabaseAPI().test_exist_by_id(image_id, imgtype)
            if test_exist:
                self.detail_page.addTab(image_id, imgtype)
        self.tag_page.page_role.do_search()
        self.tag_page.page_source.do_search()
    
    def clear_refresh(self):
        """清空并刷新"""
        self.search_page.clear()
        routekeys = self.detail_page.tabs
        rli = list(routekeys)
        for key in rli:
            pattern = r"d(\d+)_(\d+)"
            match = re.match(pattern, key)
            imgtype = int(match.group(1))  # 第一个括号匹配的内容
            image_id = int(match.group(2))  # 第二个括号匹配的内容
            self.detail_page.closeTab(self.detail_page.tabBar.items.index(self.detail_page.tabBar.tab(key)))
            test_exist = DatabaseAPI().test_exist_by_id(image_id, imgtype)
            if test_exist:
                self.detail_page.addTab(image_id, imgtype)
    
    def refresh_tag_page(self):
        """刷新标签页"""
        self.tag_page.page_role.do_search()
        self.tag_page.page_source.do_search()

    def refresh_setting_page(self):
        """刷新设置页"""
        self.setting_page.refresh()

    def start_add_single_source_process(self, li, name):
        """启动指定名称的导入线程"""
        # 检查是否已存在同名线程
        if name in self.active_workers:
            w = MessageBox(
                "警告",
                f"名为 '{name}' 的导入任务已在运行中",
                self
            )
            w.exec()
            return

        # 创建线程和工作者
        thread = QThread()
        worker = AddSourceWorker(li, name)
        worker.moveToThread(thread)
        
        # 连接信号
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        worker.progress.connect(lambda: None)
        
        # 设置线程对象名称（可选，便于调试）
        thread.setObjectName(f"ImportThread-{name}")
        
        # 存储线程信息
        self.active_workers[name] = {
            'thread': thread,
            'worker': worker,
            'running': True
        }
        
        # 启动线程
        thread.start()
        
        # 更新UI
        self.setting_page.add_import_task(name)

    def terminate_process(self, name):
        """终止指定名称的导入线程"""
        print(f"终止{name}导入任务")
        if name not in self.active_workers:
            return

        worker_info = self.active_workers[name]
        if worker_info['running']:
            worker_info['worker'].stop()
            worker_info['thread'].quit()
            worker_info['thread'].wait()
            
            # 更新状态
            worker_info['running'] = False
            
            # 从活跃字典中移除
            del self.active_workers[name]
            
            # 更新UI
            DatabaseAPI.pause_spider(name)
            self.setting_page.remove_import_task(name)
            self.setting_page.all_spider.refresh()
            
            w = MessageBox(
                "信息",
                f"已终止导入任务: {name}",
                self
            )
            w.exec()

    def _on_worker_finished(self, name):
        """线程完成时的处理"""
        if name in self.active_workers:
            worker_info = self.active_workers[name]
            if worker_info['running']:
                worker_info['thread'].quit()
                worker_info['thread'].wait()
                del self.active_workers[name]
                
                # 更新UI
                DatabaseAPI.pause_spider(name)
                self.setting_page.complete_import_task(name)
                self.setting_page.all_spider.refresh()
                
                # 刷新数据
                self.refresh()

    def _on_worker_error(self, error_msg, name):
        """线程出错时的处理"""
        w = MessageBox(
            "错误",
            f"导入任务 '{name}' 出错: {error_msg}",
            self
        )
        w.exec()
        DatabaseAPI.pause_spider(name)
        self._on_worker_finished(name)
        self.setting_page.all_spider.refresh()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())