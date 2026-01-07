import PyQt6.QtWidgets as Qtw
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as Qtc
import PyQt6.QtMultimedia as Qtmedia
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtQml import QQmlApplicationEngine


import json
import os
import shutil
import requests
import threading
from functools import partial
# from io import BytesIO

from scraper import Scraper, ScraperLight
from settings import Settings
from DrawBoard import DrawingBoard
from networking import Game

app = Qtw.QApplication([])




class MainWindow(Qtw.QMainWindow):

    settings_file = os.path.join(os.path.dirname(__file__), '../', 'settings.json')
    with open(settings_file, 'r') as file:
        settings_dict = json.load(file)
        searchList = settings_dict["searchList"]
        colorTheme = settings_dict["color_theme"]
        colorOptions = settings_dict["colorOptions"]
        auto_scroll = settings_dict["auto_scroll"]
        backgroundTheme = settings_dict["backgroundTheme"]
        originalSizedImages = settings_dict["originalSize"]
        tool_tips = settings_dict["tool_tips"]

    def __init__(self):
        super().__init__()


        self.monolist = self.searchList
        self.styles = {}
        self.setStyleSheet("font-family: helvetica;")
        self.setWindowTitle("Board View")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '../assets', 'pencil.png')))
        self.setGeometry(100, 100, 800, 600)
        self.setSizePolicy(Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Expanding)
        
        try:
            requests.get(self.backgroundTheme)
            is_url = True
        except:
            is_url = False

        if is_url:
            self.styles["background-image"] = "background-image: url(" + str(self.backgroundTheme) + ");"
            
        elif '#' in self.backgroundTheme:
            self.styles["background-color"] =  "background-color:" + str(self.backgroundTheme) + ";"

        else:
            self.styles["background-image"] = ""
            self.styles["background-color"] = ""
        

        for k in self.styles:
            self.updateStyleSheet(self.styles[k])

        self.showFrame("StartPage")
       
    def isLight(self, color):
        hex_string = color[1:]
        if int(hex_string, 16) > 8388607:
            return True
        else:
            return False
        
    def reloadStyles(self):
        settings_file = os.path.join(os.path.dirname(__file__), '../', 'settings.json')
        with open(settings_file, 'r') as file:
            settings_dict = json.load(file)
            self.colorTheme = settings_dict["colorTheme"]
            self.colorOptions = settings_dict["colorOptions"]
            self.auto_scroll = settings_dict["auto_scroll"]
            self.backgroundTheme = settings_dict["backgroundTheme"]
            self.originalSizedImages = settings_dict["originalSize"]
            self.tool_tips = settings_dict["tool_tips"]

        if "https://" in self.backgroundTheme:
            self.styles["background-image"] = "background-image: url(" + str(self.backgroundTheme) + ");"
            
        elif '#' in self.backgroundTheme:
            self.styles["background-color"] =  "background-color:" + str(self.backgroundTheme) + ";"

        else:
            self.styles["background-image"] = ""
            self.styles["background-color"] = ""

        notify_change_event = monolistChange(self.monolist)
        app.postEvent(self, notify_change_event)
        

        self.setStyleSheet("font-family: helvetica;")
        for k in self.styles:
            self.updateStyleSheet(self.styles[k])

        


    def showFrame(self, page_name, whatToShow=None):
        
        frame = StartPage(self)
        
        # if page_name == "SearchPage":
        #     frame = SearchPage(self, whatToShow)
        #     frame.whatToPull(whatToShow)
        if page_name == "Saves":
            frame = Saves(self)
        if page_name == "BoardView":
            frame = GameWrapper(self)
        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        self.layout().addWidget(frame)
        self.setCentralWidget(frame)
 
    def updateStyleSheet(self, new_style):
        current = self.styleSheet()

        if new_style not in current:
            combined_sheet = current + new_style
            self.setStyleSheet(combined_sheet)

class StartPage(Qtw.QFrame):
    def __init__(self, master):
        super().__init__()
                                                                                                                    #Page with start screen and buttons to the other pages
        self.master = master
        self.setStyleSheet("")
        self.installEventFilter(self)

       

        v_lay = Qtw.QVBoxLayout(self) #Vertical box layout

        my_label = Qtw.QLabel("Board View")

        my_label.setFont(QtGui.QFont("Helvetica", 18))
        my_label.setAlignment(Qtc.Qt.AlignmentFlag.AlignHCenter)

        v_lay.addWidget(my_label)
                                                                                                                        #selectible site list combobox
        self.my_combo = Qtw.QComboBox(self)
        self.my_combo.insertItems(0, self.master.monolist.keys())
        v_lay.addWidget(self.my_combo)
        h_lay = Qtw.QHBoxLayout()
        v_lay.addLayout(h_lay)

                                                                                                                        #Primary Page Navigation Buttons
        start_btn = Qtw.QPushButton("BoardView")
        if self.master.colorTheme:
            start_btn.setStyleSheet("border: 1px solid " + self.master.colorTheme + ";")
        start_btn.clicked.connect(lambda: master.showFrame("BoardView", self.master.monolist[self.my_combo.currentText()]))
        # top_btn = Qtw.QPushButton("Top")
        # if self.master.colorTheme:
        #     top_btn.setStyleSheet("border: 1px solid " + self.master.colorTheme + ";")
        # top_btn.clicked.connect(lambda: master.showFrame("TopPage", self.master.monolist[self.my_combo.currentText()]))
        saves_btn = Qtw.QPushButton("Saves")
        if self.master.colorTheme:
            saves_btn.setStyleSheet("border: 1px solid " + self.master.colorTheme + ";")
        saves_btn.clicked.connect(lambda: master.showFrame("Saves", self.master.monolist[self.my_combo.currentText()]))

        settings_tab = Settings(self.master)
        settings_btn = Qtw.QPushButton("Settings")
        if self.master.colorTheme:
            settings_btn.setStyleSheet("border: 1px solid " + self.master.colorTheme + ";")
        settings_btn.clicked.connect(settings_tab.show) 

        h_lay.addWidget(start_btn)
        #h_lay.addWidget(top_btn)
        h_lay.addWidget(saves_btn)
        h_lay.addWidget(settings_btn)



        # self.layout().addWidget(self.container)
    def updateCombo(self):
        self.my_combo.clear()
        self.my_combo.insertItems(0, self.master.monolist.keys())

    def eventFilter(self, source, event):
        if event.type() == monolistChange.TYPE:
            self.updateCombo()
            return True
        return super().eventFilter(source, event)
    
class monolistChange(Qtc.QEvent):
    TYPE = Qtc.QEvent.Type(Qtc.QEvent.registerEventType())
    def __init__(self, new_monolist):
        super().__init__(self.TYPE)
        self.new_monolist = new_monolist
        
    

class GameWrapper(Qtw.QFrame):
    game : Game
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.setSizePolicy(Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Expanding)
        vbox = Qtw.QVBoxLayout(self)
        self.game = Game()
        self.Board = DrawingBoard(self)
        self.game.set_board(self.Board)

        self.Board.new_drawing.connect(self.send_board_data) #Connect signal from DrawingBoard to send_board_data method


        vbox.addWidget(self.Board, stretch=8)
        self.pallette = ColorPallette(self) #ColorPallette widget (GridLayout)
        
        self.pallette.change_color_event.connect(self.Board.color_change_event)
        vbox.addWidget(self.pallette, stretch=1, alignment=Qtc.Qt.AlignmentFlag.AlignLeft)
        
        back_btn = Qtw.QPushButton("Back")
        back_btn.clicked.connect(self.end_game)
        vbox.addWidget(back_btn, stretch=1)
        self.setLayout(vbox)
    def end_game(self):
        self.game.stop_game()
        self.pallette.deleteLater()
        self.deleteLater()
        self.master.showFrame("StartPage")
    @Qtc.pyqtSlot(list, name="send_board_data")
    def send_board_data(self, data):
        self.game.send_board_data(data)

class ColorPallette(Qtw.QWidget):
    change_color_event = Qtc.pyqtSignal(QtGui.QColor, name="color_change_event")
    COLOR_OPTIONS = [QtGui.QColor("#000000"), 
        QtGui.QColor("#FFFFFF"),
        QtGui.QColor("#ff0000"),
        QtGui.QColor("#ff5e00"),
        QtGui.QColor("#ffbb00"), 
        QtGui.QColor("#e6ff00"),
        QtGui.QColor("#88ff00"),
        QtGui.QColor("#2aff00"),
        QtGui.QColor("#00ff33"),
        QtGui.QColor("#00ff90"),
        QtGui.QColor("#00ffee"),
        QtGui.QColor("#00b3ff"),
        QtGui.QColor("#0055ff"),
        QtGui.QColor("#0800ff"),
        QtGui.QColor("#6600ff"),
        QtGui.QColor("#c400ff"),
        QtGui.QColor("#ff00dd"),
        QtGui.QColor("#ff0080")]
    def __init__(self, master):
        super().__init__()
        self.master = master
        layout = Qtw.QGridLayout()
        for i in range(2):
            for j in range(len(self.COLOR_OPTIONS)//2): #Should be symmetrical anyway so this should be fine
                btn = Qtw.QPushButton()
                btn.setStyleSheet(f"background-color: {self.COLOR_OPTIONS[i*8 + j].name()}; border: none;")
                btn.clicked.connect(partial(self.changeColor, self.COLOR_OPTIONS[i*8 + j])) #color needs to be saved after this loop ends
                layout.addWidget(btn, i, j)
        self.setLayout(layout)
    
    def changeColor(self, color : QtGui.QColor):
        print("SIGNAL::Color changed to:", color.name())
        self.change_color_event.emit(color)



    


class ImageViewer(Qtw.QWidget):
    
    def __init__(self, master, flag):
        super().__init__(master)
        self.imageHandlingFlag = flag
        self.master = master
        self.index=0
        self.master_layout = None
        self.setFixedSize(self.master.width(), self.master.height())

        self.setWindowFlags(Qtc.Qt.WindowType.WindowStaysOnTopHint)

        self.main_layout_hbox = Qtw.QHBoxLayout()
        
        self.main_layout_hbox.setGeometry(self.geometry())

        leftIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '../assets/d_arrow_left_light.png'))
        leftbtn = Qtw.QPushButton()
        leftbtn.setStyleSheet("background:None; min-width:40px; min-height:40px;")
        leftbtn.setIcon(leftIcon)
        leftbtn.clicked.connect(self.decrementView)

        rightIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '../assets/d_arrow_right_light.png'))
        rightbtn = Qtw.QPushButton() 
        rightbtn.setStyleSheet("background:None; min-width:40px; min-height:40px;")
        rightbtn.setIcon(rightIcon)
        rightbtn.clicked.connect(self.incrementView)

        self.main_layout_hbox.addWidget(leftbtn, stretch=1, alignment=Qtc.Qt.AlignmentFlag.AlignLeft)
        self.main_layout_hbox.addSpacerItem(Qtw.QSpacerItem(20,20,Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Minimum))
        self.main_layout_hbox.addWidget(rightbtn, stretch=1, alignment=Qtc.Qt.AlignmentFlag.AlignRight)
        
        self.setLayout(self.main_layout_hbox)
        self.installEventFilter(self)
        self.hide()
    def initalizeView(self, layout, index):
        if not self.isVisible():
            self.index = index
            self.master_layout = layout
            if self.imageHandlingFlag == True:
                show_widget = self.copyWidget_original_size(layout.itemAt(self.index).widget())
            else:
                show_widget = self.copyWidget(layout.itemAt(self.index).widget())
            self.main_layout_hbox.removeWidget(self.main_layout_hbox.itemAt(1).widget())
            self.main_layout_hbox.insertWidget(1, show_widget, stretch=10, alignment= Qtc.Qt.AlignmentFlag.AlignCenter)
            self.show()
            self.raise_()
    def incrementView(self):
        if self.index+1 < self.master_layout.count():
            self.index += 1
            if self.imageHandlingFlag == True:
                next_widget = self.copyWidget_original_size(self.master_layout.itemAt(self.index).widget())
            else:
                next_widget = self.copyWidget(self.master_layout.itemAt(self.index).widget())
            
            self.main_layout_hbox.removeWidget(self.main_layout_hbox.itemAt(1).widget())
            self.main_layout_hbox.insertWidget(1, next_widget, stretch=10, alignment= Qtc.Qt.AlignmentFlag.AlignCenter)
    def decrementView(self):
        if self.index-1 >= 0:
            self.index -= 1
            if self.imageHandlingFlag == True:
                next_widget = self.copyWidget_original_size(self.master_layout.itemAt(self.index).widget())
            else:
                next_widget = self.copyWidget(self.master_layout.itemAt(self.index).widget())            

            self.main_layout_hbox.removeWidget(self.main_layout_hbox.itemAt(1).widget())
            self.main_layout_hbox.insertWidget(1, next_widget, stretch=5, alignment= Qtc.Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resizeWidget()
    def resizeWidget(self):
        self.setFixedSize(self.master.width(), self.master.height())
        # self.main_layout_hbox.setGeometry(self.geometry())

        
       
    def eventFilter(self, source, event):
        if source == self:
            if event.type() == Qtc.QEvent.Type.MouseButtonPress:
                click_pos = event.pos()
                if not self.withinBounds(click_pos):
                    self.hide()
        return super().eventFilter(source, event)
    
    def withinBounds(self, click_pos):
        for i in range(self.main_layout_hbox.count()):
            item = self.main_layout_hbox.itemAt(i)
            widget = item.widget()
            if widget and widget.geometry().contains(click_pos):
                return True
        return False
    

    def copyWidget_original_size(self, widget):
        if widget is None:
            return None
        if isinstance(widget, videoContainer):
            new_widget = self.master.copyVid(widget)
            
            return new_widget
        elif isinstance(widget, Qtw.QLabel) and isinstance(widget.movie(), QtGui.QMovie):
            new_widget = self.master.copyMovie(widget)

            return new_widget

        elif isinstance(widget, Qtw.QLabel):
            new_widget = self.master.copyImg(widget)

            return new_widget
        
        new_widget = Qtw.QWidget()
        if widget.layout() and not widget.layout().isEmpty():
            new_layout = self.copyLayout(widget.layout())
            new_widget.setLayout(new_layout)

        
        return new_widget
    
    def copyWidget(self, widget):
        if widget is None:
            return None
        if isinstance(widget, videoContainer):
            new_widget = self.master.copyVid(widget)
            new_widget.setMaximumHeight(int(self.height()*0.9))
            new_widget.setMaximumWidth(int(self.width()*0.9))
            new_widget.setFixedSize(int(self.width()*0.9), int(self.height()*0.9))
            return new_widget
        elif isinstance(widget, Qtw.QLabel) and isinstance(widget.movie(), QtGui.QMovie):
            new_widget = self.master.copyMovie(widget)
            new_widget.setMaximumHeight(int(self.height()*0.9))
            new_widget.setMaximumWidth(int(self.width()*0.9))
            new_widget.setFixedSize(int(self.width()*0.9), int(self.height()*0.9))

            return new_widget

        elif isinstance(widget, Qtw.QLabel):
            new_widget = self.master.copyImg(widget)
            new_widget.setMaximumHeight(self.height())
            new_widget.setMaximumWidth(self.width())
            new_widget.setFixedSize(int(self.width()*0.9), int(self.height()*0.9))

            return new_widget
        
        new_widget = Qtw.QWidget()
        if widget.layout() and not widget.layout().isEmpty():
            new_layout = self.copyLayout(widget.layout())
            new_widget.setLayout(new_layout)

        
        return new_widget

    def copyLayout(self, layout):
        new_layout = Qtw.QVBoxLayout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if isinstance(item, Qtw.QWidgetItem):
                if item.widget():
                    new_layout.addWidget(self.copyWidget(item.widget()))
            elif isinstance(item, Qtw.QLayoutItem):
                if item.layout() and not item.layout().isEmpty():
                    new_layout.addLayout(self.copyLayout(item.layout()))
        return new_layout
    
class videoContainer(Qtw.QWidget):
    def __init__(self, json):
        super().__init__()
        self.json = json

class ButtonWithState(Qtw.QPushButton):
    state = 0
    def __init__(self):
        super().__init__()

class GifWorker(Qtc.QObject):
    handle_gif = Qtc.pyqtSignal(object, str)
    finished = Qtc.pyqtSignal()
    def __init__(self, label, json):
        super().__init__()
        self.json = json
        self.label = label
        
        
    def run(self):
        
        self.threadActive = True

        os.makedirs('video_assets', exist_ok=True)
        try:
            file_url = self.json['file_url']
        except:
            file_url = self.json['@file_url']
        if not os.path.exists(os.path.join(os.path.dirname(__file__), '../', 'video_assets', os.path.basename(file_url))):
            filename = os.path.join(os.path.dirname(__file__), '../', 'video_assets', os.path.basename(file_url))
            res = requests.get(file_url, stream=True, timeout=10)

            with open(filename, 'wb') as file:
                file.write(res.content)

        else:
            filename = os.path.join(os.path.dirname(__file__), '../', 'video_assets', os.path.basename(file_url))

        self.handle_gif.emit(self.label, filename)
        print("Inner Thread" + str(threading.get_ident()))

        self.finished.emit()
  
    def stop(self):
        self.threadActive = False
        self.quit()
class VidWorker(Qtc.QThread):
    handle_gif = Qtc.pyqtSignal(object, str)
    finished = Qtc.pyqtSignal()


class Worker(Qtc.QObject):
    #image data, image description json, isVideo list [true/false, preview bytes], isGif bool
    progress = Qtc.pyqtSignal(bytes, dict, list, bool, name="imageLoad")
    finished = Qtc.pyqtSignal(name="imageLoad")

    def __init__(self, scraper):
        super().__init__()
        self.scraper = scraper
        self.stop = False
        
    def run(self):
        #array of jsons with file paths
        catalog = self.scraper.catalog()
        
        if catalog:
            for i in range(len(catalog)):
                if self.stop:
                    break
                try:
                    with open(catalog[i]['file_url'], 'rb') as file:
                        data = file.read()
                    self.progress.emit(data, catalog[i], self.isVideo(catalog[i]['file_url'], catalog[i]), self.isGif(catalog[i]['file_url']))

                except Exception as e:
                    print(e)
                    continue
        self.finished.emit()

    def isVideo(self, url, json):

        url = url.lower()
        isVideo = False
        video_extensions =['.mp4', '.avi', '.mov', '.mkv']
        for v in video_extensions:
            if url.endswith(v):
                isVideo = True
        preview = None
        if isVideo:
            if 'preview_url' in json.keys():
                if 'video_preview' in json.keys():
                    with open(json['video_preview'], 'rb') as video_preview:
                        preview = video_preview.read()

        return [isVideo, preview]
    def isGif(self, url):    
        url = url.lower()
        if url.endswith('.gif'):
            return True
        else:
            return False

class BottomWorker(Qtc.QObject):
    #should return list of image category names and counts
    progress = Qtc.pyqtSignal(list, list, name="bottom")
    show = Qtc.pyqtSignal(bool, name="showHide")
    finished = Qtc.pyqtSignal(name="bottom")
    # finished = Qtc.pyqtSignal(name="bottom")
    def __init__(self, scraper : Scraper):
        super().__init__()
    def run(self, input_string):
        searchFlag = True 
        if input_string is None:      
            searchFlag = False
        elif not self.validSearch(input_string):
            searchFlag = False
        
        if searchFlag:
            pass
        
        
        #temporary
        self.progress.emit([], [])


        self.finished.emit()
    def validSearch(self, search_string):
        if search_string and search_string.strip():
            return True
        return False

class ClickableLabels(Qtw.QLabel):
    clicked = Qtc.pyqtSignal(object, int)

    def __init__(self, index, container):
        super().__init__()
        self.index = index
        self.container = container
        self.installEventFilter(self)
    def eventFilter(self, source, event):
        if source == self:
            if event.type() == Qtc.QEvent.Type.MouseButtonDblClick:
                self.clicked.emit(self.container, self.index)
                return True
        return super().eventFilter(source, event)


class Saves(Qtw.QFrame):
    def switch_back(self):
        self.master.showFrame("StartPage")
    def __init__(self, master):
        super().__init__()
        self.master = master
        
        
        self.save_widget = self.makeDefaultCentWidget()
        self.save_widget.setMinimumSize(600,400)
        save_hbox = Qtw.QHBoxLayout()
        save_hbox.addWidget(self.save_widget)
        self.save_layout = Qtw.QVBoxLayout()
        
        
        #top left back button
        back_btn = Qtw.QPushButton("Back")
        back_btn.clicked.connect(self.switch_back)
        self.save_layout.addWidget(back_btn, alignment=Qtc.Qt.AlignmentFlag.AlignLeft | Qtc.Qt.AlignmentFlag.AlignTop, stretch=1)

        self.save_layout.addStretch(1)
        #Add save grid
        self.save_widget.setSizePolicy(Qtw.QSizePolicy.Policy.Expanding,Qtw.QSizePolicy.Policy.Expanding)
        self.save_layout.addLayout(save_hbox, stretch=10)
        #center grid between buttons
        self.save_layout.addStretch(1)

        #default 4x4 grid
        self.grid_cols = 4
        self.grid_rows = 4
        #light scrape indexing
        self.scraper = ScraperLight()
        #Pagination
        self.image_count = self.scraper.getLength()
        self.page_count = (self.image_count // (self.grid_cols * self.grid_rows)) + 1 #in case of remainder
        self.current_page = 0
        
        #Add Button for navigating between pages
        self.page_navigation_layout = Qtw.QHBoxLayout()
        self.cur_page_btn = Qtw.QPushButton("Current Page")
        self.prev_page_btn = Qtw.QPushButton("Previous Page")
        self.next_page_btn = Qtw.QPushButton("Next Page")
        self.prev_page_label = Qtw.QLabel(f"Page {self.current_page}")
        self.cur_page_label = Qtw.QLabel(f"Page {self.current_page + 1}")
        self.next_page_label = Qtw.QLabel(f" of {self.page_count + 2}")
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.next_page_btn.clicked.connect(self.next_page)

        self.page_navigation_layout.addWidget(self.prev_page_btn)
        self.page_navigation_layout.addWidget(self.cur_page_btn)
        self.page_navigation_layout.addWidget(self.next_page_btn)
        #Populate the initial grid
        self.get_page()

        #Add buttons to layout
        self.save_layout.addLayout(self.page_navigation_layout, stretch=2)
        self.save_widget.resized.connect(self.resize_grid)
        self.save_layout.setSpacing(10)
        self.setSizePolicy(Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Expanding)
        
        self.setLayout(self.save_layout)
    def next_page(self):
        if self.current_page + 1 < self.page_count:
            self.current_page += 1
            self.get_page()
    def prev_page(self):
        if self.current_page - 1 >= 0:
            self.current_page -= 1
            self.get_page()
            if self.current_page == 0:
                self.prev_page_btn.setEnabled(False)
            else:
                self.prev_page_btn.setEnabled(True)
    def get_page(self):
        start_index = self.current_page * self.grid_cols * self.grid_rows
        end_index = start_index + (self.grid_cols * self.grid_rows)
        images = self.scraper.grab_catalog_range(start_index, end_index)
        for i in range(self.grid_rows):
            for j in range(self.grid_cols):
                img_index = i * self.grid_cols + j
                if img_index < len(images):
                    img_json = images[img_index]
                    img_path = img_json['file_url']
                    #Create image widget and add to grid
                    img = QtGui.QImage()
                    img.load(img_path)
                    pixmap = QtGui.QPixmap.fromImage(img)
                    if not pixmap.isNull():
                        print("Loaded image for saves grid:", img_path)
                        clabel = ClickableLabels(img_index, self.save_widget.layout())
                        clabel.setProperty("original_pixmap", pixmap)
                        scaled_pixmap = pixmap.scaled(self.save_widget.width()//(self.grid_cols), self.save_widget.height()//(self.grid_rows), Qtc.Qt.AspectRatioMode.IgnoreAspectRatio, Qtc.Qt.TransformationMode.SmoothTransformation)
                        clabel.setPixmap(scaled_pixmap)
                        self.save_widget.layout().addWidget(clabel, i, j)
                    else:
                        self.save_widget.layout().addWidget(Qtw.QLabel(), i, j)
                else:
                    self.save_widget.layout().addWidget(Qtw.QLabel(), i, j)
    def makeDefaultCentWidget(self):
        c = IndexedWidgets(0, self)
        
        savedGrid = SaveGrid(c)
        if '#' in self.master.backgroundTheme:
            color = QtGui.QColor(self.master.backgroundTheme)
            r = color.red()
            g = color.green() + 20
            b = color.blue()
            r = min(255, r)
            g = min(255, g)
            b = min(255, b)
            shift = QtGui.QColor(r,g,b).name()
            c.setStyleSheet("background-color:" + shift)
        elif not self.master.backgroundTheme:
            c.setStyleSheet("background-color:#27282b")
        
        c.setLayout(savedGrid)
        return c
    @Qtc.pyqtSlot(name="resize_index_widget")
    def resize_grid(self):
        grid = self.save_widget.layout()
        if not grid:
            return
        for i in range(grid.count()):
            item = grid.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, ClickableLabels):
                original_pixmap = widget.property("original_pixmap")
                if original_pixmap:
                    scaled_pixmap = original_pixmap.scaled(self.save_widget.width()//(self.grid_cols), self.save_widget.height()//(self.grid_rows), Qtc.Qt.AspectRatioMode.IgnoreAspectRatio, Qtc.Qt.TransformationMode.SmoothTransformation)
                    widget.setPixmap(scaled_pixmap)
        
    
class IndexedWidgets(Qtw.QWidget):
    resized = Qtc.pyqtSignal(name="resize_index_widget")
    def __init__(self, index, master=None):
        super().__init__(master)
        self.index = index
    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        self.resized.emit()
         
class SaveGrid(Qtw.QGridLayout):
    def __init__(self, master=None):
        super().__init__(master)
        #self.setContentsMargins(24,24,24,24)
        
        if isinstance(master, IndexedWidgets):
            glow = Qtw.QGraphicsDropShadowEffect(master)
            glow.setBlurRadius(50)
            glow.setOffset(0,0)
            glow.setColor(QtGui.QColor(28, 100, 212, 1))
            master.setGraphicsEffect(glow)


engine = QQmlApplicationEngine()

we = MainWindow()





we.show()
app.exec()

app.exit()
if isinstance(we.centralWidget(), GameWrapper):
    we.centralWidget().end_game()
    we.centralWidget().deleteLater()



print("Goodbye")
