#Optional feature to use YOLO for catalog to search through images
import PyQt6.QtWidgets as Qtw
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as Qtc
import PyQt6.QtMultimedia as Qtmedia
from PyQt6.QtMultimediaWidgets import QVideoWidget

from scraper import Scraper, ScraperLight
from settings import Settings
from CustomAtomic import AtomicInteger, AtomicClockVLayout
from functools import partial
import threading
import os

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
