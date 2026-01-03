import PyQt6.QtWidgets as Qtw
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as Qtc

class DrawingBoard(Qtw.QWidget):
    def __init__(self, master):
        super().__init__()
        self.master = master
        