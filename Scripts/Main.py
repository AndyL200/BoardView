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

app = Qtw.QApplication([])


class AtomicInteger:
    def __init__(self, initial=0):
        self.value = initial
        self.lock = threading.Lock()
    def increment(self):
        with self.lock:
            self.value+=1

    def decrement(self):
        with self.lock:
            self.value-=1

    def set(self, val):
        with self.lock:
            self.value = val
            

    def get(self):
        with self.lock:
            return self.value
        


class MainWindow(Qtw.QMainWindow):

    settings_file = os.path.join('origin', 'settings.json')
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
        self.setWindowIcon(QtGui.QIcon(os.path.join('origin', 'assets', 'pencil.png')))
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
        settings_file = os.path.join('origin', 'settings.json')
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
        
        if page_name == "SearchPage":
            frame = SearchPage(self, whatToShow)
            frame.whatToPull(whatToShow)
        if page_name == "Saves":
            frame = Saves(self)
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
        start_btn = Qtw.QPushButton("Search")
        if self.master.colorTheme:
            start_btn.setStyleSheet("border: 1px solid " + self.master.colorTheme + ";")
        start_btn.clicked.connect(lambda: master.showFrame("SearchPage", self.master.monolist[self.my_combo.currentText()]))
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
        
    

class SearchPage(Qtw.QFrame):
    comp = ""
    def __init__(self, master, search):
        super().__init__()
        self.setSizePolicy(Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Expanding)
        
        self.gifThread = Qtc.QThread()



        self.master = master
        self.scraper = Scraper(search)
        self.vidInt = AtomicInteger()
        
                                                                                                                        #atomic integer for image loading
        self.loading = AtomicInteger()
                                                
        
                                                                                                                        #making a container for the images on the page
        self.imgContain = Qtw.QWidget()
        self.scr = Qtw.QScrollArea()
        self.scr.setWidgetResizable(True)
                                                                                                                        #thread for image loading
        self.t = Qtc.QThread()
        
            
        


        self.scr.setWidget(self.imgContain)

        self.scr.verticalScrollBar().valueChanged.connect(self.checkScroll)
       
        self.vbox = AtomicClockVLayout(self.imgContain)
        self.vbox.setAlignment(Qtc.Qt.AlignmentFlag.AlignHCenter)
        


        if self.master.auto_scroll:
            
            self.autoScrollTimer = Qtc.QTimer()
            self.autoScrollTimer.setInterval(100)
            self.autoScrollTimer.setSingleShot(False)
            self.autoScrollTimer.timeout.connect(self.auto_scr)
            self.auto_scr()

        self.mainLayout = Qtw.QVBoxLayout(self)

                                                                                                                        #Bottom Page Navigation
        self.bottomWidget = Qtw.QWidget()
        self.hbox = Qtw.QHBoxLayout()
        back_btn = Qtw.QPushButton(text="Back")
        if self.master.tool_tips:
            back_btn.setToolTip("Go Back to Home Page")
        back_btn.setStyleSheet("""
                            float:left;
                               """)
        back_btn.clicked.connect(lambda: self.switchBack())
        back_layout = Qtw.QHBoxLayout()
        back_layout.addWidget(back_btn)

                                                                                                                        #tag search thread
        self.bottomNavThread = Qtc.QThread()
        self.finding = AtomicInteger()

                                                                                             #Input Group
        input_group = Qtw.QVBoxLayout()

        self.image_search = Qtw.QLineEdit()
        if self.master.tool_tips:
            self.image_search.setToolTip("Search for images here. Type as many as you want and press return on the keyboard")

        grid_possible = Qtw.QGridLayout()
        
        
        self.poss_widget = Qtw.QWidget()
        self.poss_widget.setLayout(grid_possible)
        if self.master.tool_tips:
            self.poss_widget.setToolTip("Possible image matches here")

        self.grid_scroll = Qtw.QScrollArea()
        self.grid_scroll.setWidget(self.poss_widget)
        
        self.grid_scroll.setWidgetResizable(True)
       
        self.grid_scroll.hide()

        input_group.addWidget(self.image_search)

        
        input_group.addWidget(self.grid_scroll)
      

       #change to a custom listener
        # cust_input_event = Qtc.QEvent()

        

        


        self.image_search.textEdited.connect(self.imageFindTime)


                                                                                                                        #Enter Group
        enter_group = Qtw.QVBoxLayout()

        mod_plus_enter = Qtw.QHBoxLayout()


        
        search_btn = Qtw.QPushButton(text="Enter")
        if self.master.tool_tips:
            search_btn.setToolTip("Search on images or other restrictions")
            

        mod_plus_enter.addWidget(search_btn)


        loaded_grid = Qtw.QGridLayout()

        self.col = 0
        self.row = 0
        self.colCount = 6
        self.gridPush = []

        enter_group.addLayout(mod_plus_enter)
        enter_group.addLayout(loaded_grid)



        self.hbox.addLayout(back_layout)
        self.hbox.addLayout(input_group)
        self.hbox.addLayout(enter_group)

        self.bottomWidget.setLayout(self.hbox)
        

        back_layout.setAlignment(Qtc.Qt.AlignmentFlag.AlignTop)
        input_group.setAlignment(Qtc.Qt.AlignmentFlag.AlignTop)
        enter_group.setAlignment(Qtc.Qt.AlignmentFlag.AlignTop)

        

        self.image_search.returnPressed.connect(lambda:self.insertIcon(self.image_search, loaded_grid))
        search_btn.clicked.connect(lambda: self.imageSearch(loaded_grid))
       

        

        self.imageViewer = ImageViewer(self, self.master.originalSizedImages)
        self.imageIndex = 0
        
        # tagComboScroll.setStyleSheet("""
        #                             background-color:white;
        #                             """)        


        



        # self.mainLayout.addWidget(self.hbox)
        print("Main GUI Thread: " + str(threading.get_ident()))                                         #Main GUI Thread Check

        self.mainLayout.addWidget(self.scr)
        self.mainLayout.addWidget(self.bottomWidget)

        self.mainLayout.setStretch(0, 10)
        self.mainLayout.setStretch(1,1)


        self.setLayout(self.mainLayout)
        self.installEventFilter(self)

    def imageSearch(self, grid):
        self.whatToPullCustom(self.image_search.text())
        self.clearWidget()
        self.loadThread()
    def auto_scr(self):
        scroll_bar = self.scr.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.value()+5)
        self.autoScrollTimer.start()

    def imageFindTime(self):
        self.timer = Qtc.QTimer()
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.openBottomNavThread(self.image_search))

        self.timer.start()


    @Qtc.pyqtSlot(bool, name="hideShow")
    def gridScrollVisibility(self, bool):
        if bool:
            self.grid_scroll.show()
        else:
            self.grid_scroll.hide()

    def switchBack(self):
        self.blockSignals(True)
        self.loading.set(1)
        self.finding.set(1)
        self.worker.stop = True
        self.t.quit()
        self.bottomNavThread.quit()
        self.t.wait()
        self.bottomNavThread.wait()
        self.mainLayout.deleteLater()                                                                                   #self layout delete later + back button functionality
        self.master.showFrame("StartPage")
        

    def openBottomNavThread(self, image_search):
        if self.bottomNavThread.isRunning():
            self.finding.set(1)
            self.bottomNavThread.quit()
            self.bottomNavThread.wait()

        self.bottomNavThread = Qtc.QThread()
        bwork = BottomWorker(self.scraper)
        bwork.progress.connect(self.bottomNavWork)
        bwork.show.connect(self.gridScrollVisibility)
        bwork.finished.connect(self.bottomNavThread.quit)
        bwork.finished.connect(bwork.deleteLater)
        bwork.moveToThread(self.bottomNavThread)

        self.bottomNavThread.started.connect(partial(bwork.run, self.finding, image_search.text().split(' ')))

        self.finding.set(0)
        self.bottomNavThread.start()

    @Qtc.pyqtSlot(list, list,  name="bottom")
    def bottomNavWork(self, names, counts):
        self.grid_scroll.setMaximumHeight(self.image_search.height()*3)
        self.grid_scroll.setMaximumWidth(self.image_search.width())

        grid = Qtw.QGridLayout()
        col = 0
        row = 0
        colCount = 2
        for i in range(len(names)):
            j=i
            h_rows = Qtw.QHBoxLayout()
            name_btn = Qtw.QPushButton(text=names[i])
            name_btn.clicked.connect(partial(self.insertText, self.image_search, names[i], self.grid_scroll))
            if self.master.colorTheme:
                if self.isLight(self.master.colorTheme):
                    name_btn.setStyleSheet(f"border-radius: 40%;font-weight: bold; background-color:{self.master.colorTheme}; color: black")
                else:
                    name_btn.setStyleSheet(f"border-radius: 40%;font-weight: bold; background-color:{self.master.colorTheme}; color: white")

            else:
                name_btn.setStyleSheet(f"border-radius: 40%;font-weight: bold; background-color:#5C9BED;")

            h_rows.addWidget(name_btn)
            if j < len(counts):
                count_label = Qtw.QLabel(text=str(counts[j]))
                if self.master.colorTheme:
                    reverse = self.reverseColor(self.master.colorTheme)
                    if self.isLight(reverse):
                        count_label.setStyleSheet(f"background-color:{reverse}; color: black;font-weight: bold;")
                    else:
                        count_label.setStyleSheet(f"background-color:{reverse}; color: white;font-weight: bold;")

                else:
                    count_label.setStyleSheet(f"background-color:#5CEDE3;font-weight: bold;")

                h_rows.addWidget(count_label)

            grid.addLayout(h_rows, row, col)
            col+=1
            if col >= colCount:
                col = 0
                row+=1

        self.poss_widget = Qtw.QWidget()
        self.grid_scroll.setWidget(self.poss_widget)
        self.poss_widget.setLayout(grid)

          
    def isLight(self, color):
        hex_string = color[1:]
        if int(hex_string, 16) > 8388607:
            return True
        else:
            return False
    def reverseColor(self, color):
        hex_string = color
        sub1 = hex_string[1] + hex_string[2]
        sub2 = hex_string[3] + hex_string[4]
        sub3 = hex_string[5] + hex_string[6]
        red = int(sub1, 16)
        green = int(sub3, 16)
        blue = int(sub2, 16)
        counter_part = "#" + str(255-red) + str(255-green) + str(255-blue)
        return counter_part
        

    def insertText(self, inp, text, scroll):
        input_string = inp.text().split(' ')
        new_input = ""
        for i in range(len(input_string)-1):
            new_input += input_string[i] + ' '
        new_input += text
        inp.setText(new_input)
        scroll.hide()
    def removeIcon(self, grid):
        button = self.sender()
        grid.removeWidget(button)
        self.gridPush.remove(button)
        button.deleteLater()
        self.restructureGrid(grid)

    def restructureGrid(self, grid):
        for i in reversed(range(grid.count())):
            grid.itemAt(i).widget().setParent(None)
        
        self.col = 0
        self.row = 0
        for w in self.gridPush:
            grid.addWidget(w, self.row, self.col)
            self.col+=1
            if self.col == self.colCount:
                self.col = 0
                self.row +=1
        

    def clearWidget(self):
      
        if self.t and self.t.isRunning():
            self.worker.stop = True
            self.t.quit()
            self.t.wait()

        self.loading.set(1)
        i = self.vbox.atom_count.get()
        while i >= 0:
            try:
                item = self.vbox.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()
            except:
                i-=1
                continue
            i-=1
        self.vbox.atom_count.set(0)
        self.imageIndex = 0
            
        
       
    def insertIcon(self, input, grid):
        inputtext = input.text().split(' ')
        inputtext = [s for s in inputtext if s.strip()]
        for s in inputtext:
                btn = Qtw.QPushButton(text=s.strip())
                btn.clicked.connect(lambda: self.removeIcon(grid))
                if self.master.colorTheme:
                    if self.isLight(self.master.colorTheme):
                        btn.setStyleSheet(f"border-radius: 25%; font-weight: bold; background-color:{self.master.colorTheme};color: black")
                    else:
                        btn.setStyleSheet(f"border-radius: 25%; font-weight: bold;background-color:{self.master.colorTheme};color: white")

                else:
                    btn.setStyleSheet(f"border-radius: 25%; font-weight: bold;background-color:#3fc4a3;")
                alreadyThereFlag = False
                for i in range(grid.count()):
                    if btn.text() == grid.itemAt(i).widget().text():
                        alreadyThereFlag = True
                        break
                if not alreadyThereFlag:
                    grid.addWidget(btn, self.row, self.col)
                    self.col+=1
                    self.gridPush.append(btn)
                    if self.col == self.colCount:
                        self.col = 0
                        self.row+=1
        # self.restructureGrid(grid)
    
    def checkScroll(self):
        scroll_bar = self.scr.verticalScrollBar()
        if scroll_bar.value() > scroll_bar.maximum() * 0.95 and not self.t.isRunning():                                                                                                                    #scraper pid
            self.loadThread()

    def whatToPullCustom(self, search):
        scap = Scraper(search)
        self.scraper = scap
        

        self.clearWidget()

        # with self.scraper.lock:
        #     self.loading.set(0)
        #     self.loadThread()
   
    def eventFilter(self, source, event):                                                                                               #event filter native SearchPage
        if source == self and event.type() == Qtc.QEvent.Type.KeyPress:
            if event.key() == Qtc.Qt.Key.Key_P:
                if self.master.auto_scroll:
                    if self.autoScrollTimer and self.autoScrollTimer.isActive():
                        print("timer stopped")
                        self.autoScrollTimer.stop()
                    elif self.autoScrollTimer and not self.autoScrollTimer.isActive():
                        self.autoScrollTimer.start()

        return super().eventFilter(source, event)
   
    def whatToPull(self, search):
        scap = Scraper(search)
        self.scraper = scap
        self.loadThread()

        # with self.scraper.lock:
        #     self.loadThread()


    def loadThread(self):
        if self.loading.get() == 0:
            self.loading.set(1)
            self.worker = Worker(self.scraper)
            self.worker.progress.connect(self.addImageToLayout)
            self.worker.finished.connect(self.t.quit)
            self.worker.finished.connect(self.worker.deleteLater)

            self.worker.moveToThread(self.t)

            self.t.started.connect(self.worker.run)
            self.t.start()

    @Qtc.pyqtSlot(bytes, dict, list, bool, name="imageLoad")
    def addImageToLayout(self, data, json, vidFlag, gifFlag):
        
        widget = Qtw.QWidget()
        widget.setFixedWidth(int(self.master.width()*0.7))
        widget.setFixedHeight(int(self.master.height()*0.9))
        
        

        inner_card_layout = Qtw.QVBoxLayout()
        inner_card_layout.setSpacing(0)
        
        label = ClickableLabels(self.imageIndex, self.vbox)
        label.setScaledContents(True)
        if self.master.tool_tips:
            label.setToolTip("Double Click for Image Viewer")
        label.clicked.connect(self.imageViewer.initalizeView)
        

        heart_icon = QtGui.QIcon('origin/assets/loveheart_empty.png')
        save_btn = ButtonWithState()
        save_btn.setIcon(heart_icon)
          
        save_btn.clicked.connect(partial(self.save_feature, json, save_btn))
    
      
        if gifFlag:                                                                                                                                     #gif worker
            
            
            gif_worker = GifWorker(label, json)
            
            gif_worker.handle_gif.connect(self.makeMovie_handleGif)
            gif_worker.finished.connect(self.gifThread.quit)
            gif_worker.finished.connect(gif_worker.deleteLater)

            gif_worker.moveToThread(self.gifThread)
            


            self.gifThread.started.connect(gif_worker.run)

            self.gifThread.start()


            
            
            
            inner_card_layout.addWidget(label)
            label.setMinimumSize(int(widget.width()*0.9), int(widget.height()*0.9))

            combos_saves_horizontal = Qtw.QHBoxLayout()
            spacer = Qtw.QSpacerItem(20,20, Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Minimum)
            combo = self.imageCombos(json)
            combos_saves_horizontal.addWidget(combo)
            combos_saves_horizontal.addSpacerItem(spacer)
            combos_saves_horizontal.addWidget(save_btn)
        
            combo.installEventFilter(self.createEventFilter(combo, combos_saves_horizontal))


            combos_saves_horizontal.setStretch(0, 5)
            combos_saves_horizontal.setStretch(1, 8)
            combos_saves_horizontal.setStretch(2, 2)
            inner_card_layout.addLayout(combos_saves_horizontal)

        elif vidFlag[0]:

            container = videoContainer(json)
            simpleLayout = Qtw.QVBoxLayout()
            is_stacked = False
            if vidFlag[1]:
                stacked = Qtw.QStackedLayout()
                preview_image = QtGui.QImage()
                preview_image.loadFromData(vidFlag[1])
                preview_pixmap = QtGui.QPixmap.fromImage(preview_image)
                preview_pixmap_scaled = preview_pixmap.scaled(preview_image.width(), preview_image.height(), aspectRatioMode=Qtc.Qt.AspectRatioMode.KeepAspectRatio, transformMode=Qtc.Qt.TransformationMode.SmoothTransformation)
                preview_label = Qtw.QLabel()
                preview_label.setScaledContents(True)
                preview_label.setPixmap(preview_pixmap_scaled)
                video = QVideoWidget()
                stacked.addWidget(preview_label)
                stacked.addWidget(video)
                video.setContentsMargins(0,0,0,0)
                preview_label.setContentsMargins(0,0,0,0)
                stacked.setContentsMargins(0,0,0,0)
                is_stacked = True
            else:
                video = QVideoWidget()

            audio = Qtmedia.QAudioOutput()
            audio.setVolume(0.5)
            audioDevice = Qtmedia.QMediaDevices.defaultAudioOutput()
            audio.setDevice(audioDevice)
            volIcon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.AudioVolumeMedium)
            volumeBtn = Qtw.QPushButton(icon=volIcon)
            #set video sink?
            audio_slider = Qtw.QSlider(video, orientation=Qtc.Qt.Orientation.Vertical)
            audio_slider.setStyleSheet("QSlider {bottom:0;} QSlider::handle:horizontal {margin: 0; height:30px; width:10px; background-color:grey;}  QSlider::grove:horizontal: {height:30px; background-color: blue; border: 1px solid #bbb;}")
            audio_slider.setRange(0,100)
            audio_slider.valueChanged.connect(lambda value: audio.setVolume(value/100))
            audio_slider.setValue(50)
            audio_slider.hide()
            volumeBtn.clicked.connect(lambda: self.sliderShow_audio(audio_slider))

            video_slider = Qtw.QSlider()
           
            video_slider.setStyleSheet("QSlider::handle:horizontal {margin: 0; height:10px; width:10px; background-color:grey;}  QSlider::grove:horizontal: {height:10px; background-color: blue; border: 1px solid #bbb;}")
            # video_slider.setFixedWidth()
            video_slider.setRange(0,100)
            
            

            player = Qtmedia.QMediaPlayer()
            # video.videoFrameChanged.connect(lambda: self.handle_video(video.videoFrame(), label))
            player.setVideoOutput(video)
            player.setAudioOutput(audio)
            player.setPlaybackRate(1.0)

            play_icon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.MediaPlaybackStart)
            play_btn = Qtw.QPushButton(icon=play_icon)
            if self.master.tool_tips:
                play_btn.setToolTip("Play video")
            if is_stacked:
                play_btn.clicked.connect(partial(self.handle_video_stack, player, play_btn, json, stacked))
            else:
                play_btn.clicked.connect(partial(self.handle_video, player, play_btn, json))


            
            video_slider.valueChanged.connect(lambda value: player.setPosition(int(player.duration()*value/100)))
            video_slider.setOrientation(Qtc.Qt.Orientation.Horizontal)

            h_box = Qtw.QHBoxLayout()
            h_box.addWidget(play_btn)
            h_box.addWidget(video_slider)
            h_box.addWidget(volumeBtn)
            h_box.addWidget(save_btn)
            h_box.setStretch(0, 1)
            h_box.setStretch(1, 8)
            h_box.setStretch(2, 1)
            h_box.setStretch(3, 1)
            
            
            
           
            # h_box.setStretch(0, 4)
            # h_box.setStretch(1,2)
            

            player.positionChanged.connect(partial(self.videoTimerStart, video_slider, player))
            
            
            
           
            
            
            
            if is_stacked:
                simpleLayout.addLayout(stacked)
            else:
                simpleLayout.addWidget(video)
            simpleLayout.addLayout(h_box)
            simpleLayout.setStretch(0,10)
            simpleLayout.setStretch(1,2)

            container.setLayout(simpleLayout)
            inner_card_layout.addWidget(container)
            inner_card_layout.addWidget(self.imageCombos(json))

            
        else:    
            img = QtGui.QImage()
            img.loadFromData(data)
            pixmap = QtGui.QPixmap.fromImage(img)
            scaled_pixmap = pixmap.scaled(img.width(), img.height(), aspectRatioMode=Qtc.Qt.AspectRatioMode.KeepAspectRatio, transformMode=Qtc.Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
            inner_card_layout.addWidget(label)

            combos_saves_horizontal = Qtw.QHBoxLayout()
            spacer = Qtw.QSpacerItem(20,20, Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Minimum)
            combos_saves_horizontal.addWidget(combo)
            combos_saves_horizontal.addSpacerItem(spacer)
            combos_saves_horizontal.addWidget(save_btn)
        

            combos_saves_horizontal.setStretch(0, 5)
            combos_saves_horizontal.setStretch(1, 8)
            combos_saves_horizontal.setStretch(2, 2)
            inner_card_layout.addLayout(combos_saves_horizontal)




        widget.setLayout(inner_card_layout)
        widget.setSizePolicy(Qtw.QSizePolicy.Policy.Expanding, Qtw.QSizePolicy.Policy.Expanding)
        self.vbox.addWidget(widget, stretch=10, alignment=Qtc.Qt.AlignmentFlag.AlignCenter)
        
        self.vbox.atom_count.increment()
        print(self.vbox.atom_count.get())
        self.imageIndex += 1
        self.loading.set(0)


   
    def copyVid(self, current_vid):
            container = Qtw.QWidget()
            simpleLayout = Qtw.QVBoxLayout()
            video = QVideoWidget()
            audio = Qtmedia.QAudioOutput()
            audio.setVolume(0.5)
            audioDevice = Qtmedia.QMediaDevices.defaultAudioOutput()
            audio.setDevice(audioDevice)
            volIcon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.AudioVolumeMedium)
            volumeBtn = Qtw.QPushButton(icon=volIcon)
            #set video sink?
            audio_slider = Qtw.QSlider(video, orientation=Qtc.Qt.Orientation.Vertical)
            audio_slider.setStyleSheet("QSlider {bottom:0;} QSlider::handle:horizontal {margin: 0; height:30px; width:10px; background-color:grey;}  QSlider::grove:horizontal: {height:30px; background-color: blue; border: 1px solid #bbb;}")
            audio_slider.setRange(0,100)
            audio_slider.valueChanged.connect(lambda value: audio.setVolume(value/100))
            audio_slider.setValue(50)
            audio_slider.hide()
            volumeBtn.clicked.connect(lambda: self.sliderShow_audio(audio_slider))

            video_slider = Qtw.QSlider()
           
            video_slider.setStyleSheet("QSlider::handle:horizontal {margin: 0; height:10px; width:10px; background-color:grey;}  QSlider::grove:horizontal: {height:10px; background-color: blue; border: 1px solid #bbb;}")
            # video_slider.setFixedWidth()
            video_slider.setRange(0,100)
            
            

            player = Qtmedia.QMediaPlayer()
            player.setVideoOutput(video)
            player.setAudioOutput(audio)

            play_icon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.MediaPlaybackStart)
            play_btn = Qtw.QPushButton(icon=play_icon)
            play_btn.clicked.connect(partial(self.handle_video, player, play_btn, current_vid.json))

            heart_icon = QtGui.QIcon('origin/assets/loveheart_empty.png')
            save_btn = ButtonWithState()
            save_btn.setIcon(heart_icon)
          
            save_btn.clicked.connect(partial(self.save_feature, current_vid.json, save_btn))
            

            h_box = Qtw.QHBoxLayout()
            h_box.addWidget(play_btn)
            h_box.addWidget(video_slider)
            h_box.addWidget(volumeBtn)
            h_box.addWidget(save_btn)
            h_box.setStretch(0, 1)
            h_box.setStretch(1, 8)
            h_box.setStretch(2, 1)
            h_box.setStretch(3, 1)
            
            
            
           
            # h_box.setStretch(0, 4)
            # h_box.setStretch(1,2)
            

            player.positionChanged.connect(partial(self.videoTimerStart, video_slider, player))

            video_slider.valueChanged.connect(lambda value: player.setPosition(int(player.duration()*value/100)))
            video_slider.setOrientation(Qtc.Qt.Orientation.Horizontal)
            
            
           
            
            
            

            simpleLayout.addWidget(video)
            simpleLayout.addLayout(h_box)
            simpleLayout.setStretch(0,5)
            simpleLayout.setStretch(1,5)

            container.setLayout(simpleLayout)
            return container
    def copyMovie(self, current_movie):
        new_movie = Qtw.QLabel()
        new_movie.setScaledContents(True)
        new_movie.setMovie(current_movie.movie())
        return new_movie
    def copyImg(self, current_img):
        new_img = Qtw.QLabel()
        new_img.setScaledContents(True)
        new_img.setPixmap(current_img.pixmap())
        return new_img    
    def createEventFilter(self, combo, hbox):
        class EventFilter(Qtc.QObject):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.combo = combo
                self.hbox = hbox
                self.master = parent
            def eventFilter(self, source, event):
                if source == self.combo:
                    if event.type() == Qtc.QEvent.Type.HoverEnter:
                        self.LabelCombosResizing(self.hbox)
                    elif event.type() == Qtc.QEvent.Type.HoverLeave:
                        self.baseLabelSizing(self.hbox)
                
                return super().eventFilter(source, event)
            def LabelCombosResizing(self, hbox):
                hbox.setStretch(0, 12)
                hbox.setStretch(1, 1)
                hbox.setStretch(2, 2)
            def baseLabelSizing(self, hbox):
                hbox.setStretch(0, 5)
                hbox.setStretch(1, 8)
                hbox.setStretch(2, 2)
        return EventFilter(self)
    def videoTimerStart(self, slider, player):
        
        if isinstance(slider, Qtw.QSlider) and player:
            if player.position() >= player.duration():
                    player.setPosition(0)
                    slider.setValue(0)
                    player.play()
            try:
                slider.blockSignals(True)
                if player.duration() > 0:
                    sliderValue = int(player.position()/player.duration()*100)
                    if sliderValue > slider.value():
                        slider.setValue(sliderValue)
                slider.blockSignals(False)
                
            except:
                return
        
    def sliderShow_audio(self, slider):
        if slider.isVisible():
            slider.hide()
        else:
            slider.show()
    # def video_sliders_handles(self, player, value):
    #     player.position = player.duration * value
    @Qtc.pyqtSlot(object, str)
    def makeMovie_handleGif(self, label, filename):
            movie = QtGui.QMovie(filename)
            
            label.setMovie(movie)
            label.movie().start()
           


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.imageViewer.resizeWidget()
        self.resizeWidget()
    def resizeWidget(self):
        for i in range(self.vbox.count()): #self.vbox.atom_count.get()? for thread safety?
            item = self.vbox.itemAt(i).widget()
            if not item.size() == Qtc.QSize(int(self.master.width()*0.7), int(self.master.height()*0.9)):
                item.setFixedSize(int(self.master.width()*0.7), int(self.master.height()*0.9))
    def handle_video_stack(self, player, btn, json, stack):
        if not player.source().isValid() or player.source().isEmpty():
            try:
                file_url = json['file_url']
            except:
                return
            
            player.setSource(Qtc.QUrl(file_url))
            stack.setCurrentWidget(player.videoOutput())
            
                # filename = os.path.join('video_assets', file_url)
                # player.setSource(Qtc.QUrl.fromLocalFile(filename))

            player.play()
        else:
            
            state = player.playbackState()
            if  state == Qtmedia.QMediaPlayer.PlaybackState.PlayingState:
                icon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.MediaPlaybackPause)
                btn.setIcon(icon)
                player.pause()
            else:
                icon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.MediaPlaybackStart)
                btn.setIcon(icon)
                player.play()
    def handle_video(self, player, btn, json):
        
        if not player.source().isValid() or player.source().isEmpty():
            try:
                file_url = json['file_url']
            except:
                return
            # os.makedirs('video_assets', exist_ok=True)
            # if not os.path.exists('video_assets' + file_url):
                # filename = os.path.join('video_assets', os.path.basename(file_url))
                # res = requests.get(file_url, stream=True, timeout=10)

                # with open(filename, 'wb') as file:
                #     file.write(res.content)
            F = Qtc.QUrl(file_url)
            player.setSource(F)
            
                # filename = os.path.join('video_assets', file_url)
                # player.setSource(Qtc.QUrl.fromLocalFile(filename))

            player.play()
        else:
            
            state = player.playbackState()
            if  state == Qtmedia.QMediaPlayer.PlaybackState.PlayingState:
                icon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.MediaPlaybackPause)
                btn.setIcon(icon)
                player.pause()
            else:
                icon = QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.MediaPlaybackStart)
                btn.setIcon(icon)
                player.play()
 
    def save_feature(self, json, btn):
        
        def nested_search(DIC, target):
            for key, value in DIC.items():
                if key == target:
                    return value
                elif isinstance(value, dict):
                    found = nested_search(value, target)
                    if found:
                        return found
            return None
        filepath = os.path.join('origin','saves.txt')
        if btn.state == 0:
            file_url = nested_search(json, 'file_url')
            print(file_url)
            if not file_url:
                return

            icon = QtGui.QIcon('origin/assets/red-heart-icon.png')
            btn.setIcon(icon)
            btn.state = 1
            alreadyThereFlag = False
            if os.path.exists(os.path.join(filepath)):
              

                with open(filepath, 'r+') as file:
                    lines = file.readlines()
                    for line in lines:
                        if line == file_url:
                            alreadyThereFlag = True
                            break
                    if not alreadyThereFlag:
                        file.seek(0, os.SEEK_END)
                        file.write(file_url + '\n')

            else:
                with open(filepath, 'w') as file:
                    file.write(file_url + '\n')

            
            downloadsFilePath = os.path.join('origin', 'saveImg')
            if not os.path.exists(downloadsFilePath):
                os.mkdir(downloadsFilePath)
           
            if not alreadyThereFlag:
                saved_img = os.path.join(downloadsFilePath, os.path.basename(file_url))
                req = requests.get(file_url, stream=True, timeout=10)
                with open(saved_img, 'wb') as file:
                    file.write(req.content)
            
        
        elif btn.state == 1 and os.path.exists(filepath):
            icon = QtGui.QIcon('origin/assets/loveheart_empty.png')
            btn.setIcon(icon)

            try:
                    file_url = json['file_url']
            except:
                    return


            with open(filepath, 'r') as file:
                lines = file.readlines()
                
            with open(filepath, 'w') as file:
                for line in lines:
                    if line.strip() != file_url:
                        file.write(line)
            if os.path.exists(os.path.join('origin', 'saveImg', os.path.basename(file_url))):
                os.remove(os.path.join('origin', 'saveImg', os.path.basename(file_url)))
            btn.state = 0
        print(os.path.exists(filepath))
        print(btn.icon())
        print(QtGui.QIcon('origin/assets/loveheart_empty.png'))


    

class AtomicClockVLayout(Qtw.QVBoxLayout):
    atom_count = AtomicInteger()
    def __init__(self, master):
        super().__init__(master)

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

        leftIcon = QtGui.QIcon('origin/assets/d_arrow_left_light.png')
        leftbtn = Qtw.QPushButton()
        leftbtn.setStyleSheet("background:None; min-width:40px; min-height:40px;")
        leftbtn.setIcon(leftIcon)
        leftbtn.clicked.connect(self.decrementView)

        rightIcon = QtGui.QIcon('origin/assets/d_arrow_right_light.png')
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
        if not os.path.exists(os.path.join('video_assets', os.path.basename(file_url))):
            filename = os.path.join('video_assets', os.path.basename(file_url))
            res = requests.get(file_url, stream=True, timeout=10)

            with open(filename, 'wb') as file:
                file.write(res.content)

        else:
            filename = os.path.join('video_assets', os.path.basename(file_url))

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
        

        self.save_layout = Qtw.QVBoxLayout()
        
        
        #top left back button
        back_btn = Qtw.QPushButton("Back")
        back_btn.clicked.connect(self.switch_back)
        self.save_layout.addWidget(back_btn, alignment=Qtc.Qt.AlignmentFlag.AlignLeft | Qtc.Qt.AlignmentFlag.AlignTop)

        self.save_layout.addStretch(1)
        #Add save grid
        self.save_layout.addWidget(self.save_widget, alignment=Qtc.Qt.AlignmentFlag.AlignHCenter)
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
        self.save_layout.addLayout(self.page_navigation_layout)
        #Resizing Filter
        self.installEventFilter(self)
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
                        scaled_pixmap = pixmap.scaled(min(pixmap.width(), self.save_widget.width()//(self.grid_cols)), min(pixmap.height(), self.save_widget.height()//(self.grid_rows)), aspectRatioMode=Qtc.Qt.AspectRatioMode.KeepAspectRatio, transformMode=Qtc.Qt.TransformationMode.SmoothTransformation)
                        clabel = ClickableLabels(img_index, self.save_widget.layout())
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
        
        c.setSizePolicy(Qtw.QSizePolicy.Policy.Expanding,Qtw.QSizePolicy.Policy.Expanding)
        c.setLayout(savedGrid)
        return c
   
    def eventFilter(self, event, source):
        return super().eventFilter(event, source)
    def resizeEvent(self, event):
        self.save_widget.resizeEvent(event)
        aspect = self.save_widget.width()/self.save_widget.height()
        new_width = event.size().width()
        new_height = event.size().height()
        if new_width/aspect <= new_height:
            new_height = new_width/aspect
        else:
            new_width = new_height * aspect
        
        self.save_widget.setMaximumSize(int(new_width), int(new_height))
        super().resizeEvent(event)
        
    
class IndexedWidgets(Qtw.QWidget):
    def __init__(self, index, master=None):
        super().__init__(master)
        self.index = index
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



print("Goodbye")
