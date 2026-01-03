import PyQt6.QtWidgets as Qtw
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as Qtc

class Settings(Qtw.QDialog):
    def __init__(self, master):
        super().__init__(master)    
        self.master = master
        self.setWindowFlag(Qtc.Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(Qtc.Qt.WidgetAttribute.WA_TranslucentBackground)

       
        self.setStyleSheet("font-size:32px; color:white; ")

        vbox = Qtw.QVBoxLayout(self)

        self.label = Qtw.QLabel(text="Settings")
        self.label
        self.label.setFont(QtGui.QFont("Arial", 40, QtGui.QFont.Weight.Bold))
        vbox.addWidget(self.label)


        self.colorLabel = Qtw.QLabel(text="ColorTheme")
        self.colorTheme = AddableCombo(self)
        for item in self.master.colorOptions:
            self.colorTheme.add_itm_wid(item)
        
        self.colorTheme.REMOVE_SIGNAL.connect(self.colorThemeChange)
        self.colorTheme.combo.setCurrentText(self.master.colorTheme)
        self.colorTheme.addBtn.clicked.connect(self.show_color_theme_add_message_box)
        self.colorTheme.plus_btn.clicked.connect(self.show_color_theme_add_message_box)
        self.colorTheme.combo.setPlaceholderText("Rgb")
        self.colorTheme.combo.currentTextChanged.connect(self.colorThemeChange)
        vbox.addWidget(self.colorLabel)
        vbox.addWidget(self.colorTheme)

        self.autoCheck = Qtw.QCheckBox(self, text="AutoScroll?")
        self.autoCheck.setToolTip("Press P to pause")
        if self.master.auto_scroll:
            self.autoCheck.setCheckState(Qtc.Qt.CheckState.Checked)
        else:
            self.autoCheck.setCheckState(Qtc.Qt.CheckState.Unchecked)
        self.autoCheck.checkStateChanged.connect(self.autoChange)
        vbox.addWidget(self.autoCheck)

        self.backgroundLabel = Qtw.QLabel(text="Custom Background Image")
        self.backGroundCustom = AddableCombo(self)


        
        if self.master.backgroundTheme:

            self.backGroundCustom.combo.setCurrentText(self.master.backgroundTheme)
            self.backGroundCustom.add_itm_wid(self.master.backgroundTheme)
        else:
            self.backGroundCustom.combo.setCurrentText("url")

        self.backGroundCustom.combo.currentTextChanged.connect(self.backgroundColorChange)
        self.backGroundCustom.REMOVE_SIGNAL.connect(self.backgroundColorChange)
        self.backGroundCustom.addBtn.clicked.connect(self.show_background_theme_add_msgbox)
        self.backGroundCustom.plus_btn.clicked.connect(self.show_background_theme_add_msgbox)
        vbox.addWidget(self.backgroundLabel)
        vbox.addWidget(self.backGroundCustom)

        self.toolTipToggle = Qtw.QCheckBox(self, text="ToolTips?")
        if self.master.tool_tips:
            self.toolTipToggle.setCheckState(Qtc.Qt.CheckState.Checked)
        else:
            self.toolTipToggle.setCheckState(Qtc.Qt.CheckState.Unchecked)
        self.toolTipToggle.checkStateChanged.connect(self.tool_tip_check)
        vbox.addWidget(self.toolTipToggle)

        self.originalSizedImages = Qtw.QCheckBox(self, text="Original Size Images?")
        if self.master.originalSizedImages:
            self.originalSizedImages.setCheckState(Qtc.Qt.CheckState.Checked)
        else:
            self.originalSizedImages.setCheckState(Qtc.Qt.CheckState.Unchecked)
        self.originalSizedImages.checkStateChanged.connect(self.og_size_image)
        vbox.addWidget(self.originalSizedImages)

        quitbtn = Qtw.QPushButton(self, text="quit")
        quitbtn.clicked.connect(self.hide)
        vbox.addWidget(quitbtn)

        self.setLayout(vbox)


    def tool_tip_check(self):
        if self.toolTipToggle.isChecked():
            self.master.tool_tips = True
        elif not self.toolTipToggle.isChecked():
            self.master.tool_tips = False
        
        self.setting_set()
    def colorThemeChange(self):
        self.master.colorTheme = self.colorTheme.combo.currentText()
        new_options = []
        for i in range(self.colorTheme.list_widg.count()):
            new_options.append(self.colorTheme.list_widg.item(i).text())
        self.master.colorOptions = new_options
        self.setting_set()
        
    def backgroundColorChange(self):
        text = self.backGroundCustom.combo.currentText()
        self.master.backgroundTheme = text
        
        self.setting_set()

    def setting_set(self):
        settings = {
                "originalSize": self.master.originalSizedImages,
                "colorTheme": self.master.colorTheme,
                "colorOptions": self.master.colorOptions,
                "auto_scroll": self.master.auto_scroll,
                "backgroundTheme": self.master.backgroundTheme,
                "searchList": self.master.searchList,
                "tool_tips": self.master.tool_tips

            }
        self.updateSettings(settings)
    def updateSettings(self, new_setting):
        with open('origin/settings.json', 'w') as file:
            json.dump(new_setting, file, indent=4)
        
        self.master.reloadStyles()

    def og_size_image(self):
        if self.originalSizedImages.isChecked():
            self.master.originalSizedImages = True
        elif not self.originalSizedImages.isChecked():
            self.master.originalSizedImages = False

        self.setting_set()


    def autoChange(self):
        if self.autoCheck.isChecked():
            self.master.auto_scroll = True
        elif not self.autoCheck.isChecked():
            self.master.auto_scroll = False



        self.setting_set()


    def show_color_theme_add_message_box(self):
        Popup = self.colorThemeAddMessageBox(self)
        
        
        Popup.show()
    class colorThemeAddMessageBox(Qtw.QDialog):
        def __init__(self, master):
            super().__init__(master)
            self.master = master
            self.setWindowFlag(Qtc.Qt.WindowType.FramelessWindowHint)
            # self.setWindowFlag(Qtc.Qt.WindowType.WindowStaysOnTopHint)
            main_layout = Qtw.QVBoxLayout()
            label = Qtw.QLabel(text="Input Color in Hex format (#FFFFFF)")
            main_layout.addWidget(label)
            hbox = Qtw.QHBoxLayout()
            input = Qtw.QLineEdit()
            input.setPlaceholderText("#FFFFFF")
            input.returnPressed.connect(lambda: self.submit(input.text().strip()))
            submit_btn = Qtw.QPushButton(text="Enter")
            submit_btn.clicked.connect(lambda: self.submit(input.text().strip()))
            hbox.addWidget(input)
            hbox.addWidget(submit_btn)
            main_layout.addLayout(hbox)
            self.setLayout(main_layout)
        def submit(self, text):
            if text and len(text) > 1:
                self.master.colorTheme.add_itm_wid(text)
                self.master.master.colorOptions.append(text)

                self.hide()
            else:
                self.hide()
    def show_background_theme_add_msgbox(self):
        Popup = self.backgroundThemeMsgBox(self)

        Popup.show()
    class backgroundThemeMsgBox(Qtw.QDialog):
        def __init__(self, master):
            super().__init__(master)
            self.master = master
            self.setWindowFlag(Qtc.Qt.WindowType.FramelessWindowHint)
            main_layout = Qtw.QVBoxLayout()
            label = Qtw.QLabel(text="Background Image or Color In Url or Hex Format")
            hbox = Qtw.QHBoxLayout()
            input = Qtw.QLineEdit()
            input.setPlaceholderText("url or #FFFFFF")
            input.returnPressed.connect(lambda: self.submit(input.text().strip()))
            submit_btn = Qtw.QPushButton(text="Enter")
            submit_btn.clicked.connect(lambda: self.submit(input.text().strip()))
            hbox.addWidget(input)
            hbox.addWidget(submit_btn)
            main_layout.addWidget(label)
            main_layout.addLayout(hbox)
            self.setLayout(main_layout)
        def submit(self, text):
            if text and len(text) > 1:
                self.master.backGroundCustom.add_itm_wid(text)
                self.hide()
            else:
                self.hide()


class AddableCombo(Qtw.QWidget):
    REMOVE_SIGNAL = Qtc.pyqtSignal()
    def __init__(self, master):
        super().__init__(master)

        self.combo = Qtw.QComboBox()
        self.combo.setDuplicatesEnabled(False)
        self.list_widg = Qtw.QListWidget()
        self.list_widg.itemClicked.connect(self.updateCombo)
        self.combo.setModel(self.list_widg.model())
        self.combo.setView(self.list_widg)

        self.action = Qtw.QWidgetAction(self) 
        self.addBtn = Qtw.QPushButton(text="Add")
        self.action.setDefaultWidget(self.addBtn)

        hbox = Qtw.QHBoxLayout()

        icon = QtGui.QIcon("origin/assets/plus_light.png")
        self.plus_btn = Qtw.QPushButton()
        self.plus_btn.setFixedSize(40,40)
        self.plus_btn.setIcon(icon)
        self.plus_btn.setStyleSheet("border: none; background: transparent; margin:10%;")
        self.plus_btn.setCursor(Qtc.Qt.CursorShape.PointingHandCursor)
        self.combo.setContextMenuPolicy(Qtc.Qt.ContextMenuPolicy.ActionsContextMenu)
        self.combo.addAction(self.action)
        inner_layout = Qtw.QHBoxLayout()
        inner_layout.addStretch()
        inner_layout.addWidget(self.plus_btn)
        self.combo.setLayout(inner_layout)

        hbox.addWidget(self.combo)
        self.setLayout(hbox)


    def add_itm_wid(self, text):
        background_item = Qtw.QListWidgetItem()
        background_item.setText(text)
        inner_background_widget = Qtw.QWidget()
        inner_background_item_layout = Qtw.QHBoxLayout()
        remove_icon = QtGui.QIcon("origin/assets/minus.png")
        remove_btn = Qtw.QPushButton(inner_background_widget)
        remove_btn.setIcon(remove_icon)
        background_item_text = Qtw.QLabel()
        background_item_text.setText(text)

        
        
        inner_background_item_layout.addWidget(background_item_text)
        inner_background_item_layout.addStretch()
        inner_background_item_layout.addWidget(remove_btn)
        inner_background_widget.setLayout(inner_background_item_layout)

        self.list_widg.addItem(background_item)
        self.list_widg.setItemWidget(background_item, inner_background_widget)
        
        n = self.list_widg.count() - 1
        remove_btn.clicked.connect(partial(self.remove_itm_wid, n))
        
    def updateCombo(self, item):
       
        text = item.text()
        self.combo.setCurrentText(text)
        
        
    def remove_itm_wid(self, n):
        self.combo.removeItem(n)
        self.combo.setCurrentText("")
       
        self.REMOVE_SIGNAL.emit()
