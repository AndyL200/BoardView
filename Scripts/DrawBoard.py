import PyQt6.QtWidgets as Qtw
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as Qtc

class DrawingBoard(Qtw.QWidget):
    
    _drawing : bool = False #mutex or lock? #Lock while drawing in progress
    _draw_thread : Qtc.QThread #thread for drawing operations


    _painter : QtGui.QPainter #Allow for drawing on the widget
    _pallette : Qtw.QWidget #color pallette widget or changing colors and styles
    pen : QtGui.QPen
    brush : QtGui.QBrush

    #Note: A Pen is used for outlines while a Brush is used for filling shapes
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.set_pen(QtGui.QPen(QtGui.QColor(0,0,0), 5)) #default pen
        self.set_brush(QtGui.QBrush(QtGui.QColor(0,0,0), Qtc.Qt.BrushStyle.SolidPattern)) #default brush

        self._painter.setPen(self.pen)
        self._painter.setBrush(self.brush)

        self._pallette = ColorPallette(self) #ColorPallette widget (GridLayout)



        self._draw_thread = Qtc.QThread()
        self._draw_thread.started.connect(self.draw)
        self._draw_thread.start()
        
        self.installEventFilter(self) #Allows for mouse events to be captured
    def set_pen(self, pen : QtGui.QPen):
        self.pen = pen
        self._painter.setPen(self.pen)
    def change_color(self, color : QtGui.QColor):
        self.pen.setColor(color)
        self.brush.setColor(color)
    def set_brush(self, brush : QtGui.QBrush):
        self.brush = brush
        self._painter.setBrush(self.brush)
    def change_style(self, style : Qtc.Qt.PenStyle):
        self.pen.setStyle(style)
    def draw(self):
        while self._drawing:
            QtGui.QCursor.pos()
    def draw(self, cached_pos):
        pass
    def eventFilter(self, source, event):
        if source == self:
            if event.type() == Qtc.QEvent.Type.MouseButtonPress:
                self._drawing = True
                return True
        return super().eventFilter(source, event)
    @Qtc.pyqtSlot()
    def penChanged(self):
        pass
    @Qtc.pyqtSlot()
    def drawEvent(self):
        pass


class ColorPallette(Qtw.QWidget):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.layout = Qtw.QGridLayout()
        self.setLayout(self.layout)