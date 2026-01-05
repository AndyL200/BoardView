import PyQt6.QtWidgets as Qtw
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as Qtc

class DrawingBoard(Qtw.QWidget):
    
    _drawing : bool = False #mutex or lock? #Lock while drawing in progress
    new_drawing : Qtc.pyqtSignal

    pen : QtGui.QPen
    brush : QtGui.QBrush

    _point_log : Qtc.QPoint = []  #Cache of points drawn since last update

    #Note: A Pen is used for outlines while a Brush is used for filling shapes
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.new_drawing = Qtc.pyqtSignal()
        self.whiteboard = QtGui.QImage(self.size(), QtGui.QImage.Format.Format_RGB32)
        self.whiteboard.fill(Qtc.Qt.GlobalColor.white)

        self.pen = QtGui.QPen(Qtc.Qt.GlobalColor.black, 3, Qtc.Qt.PenStyle.SolidLine, Qtc.Qt.PenCapStyle.RoundCap, Qtc.Qt.PenJoinStyle.RoundJoin)
        self.brush = QtGui.QBrush(Qtc.Qt.GlobalColor.black)

        self._drawing = False
        self.last_pos = Qtc.QPoint()

        
        
        self.installEventFilter(self) #Allows for mouse events to be captured
    
    
    def set_pen(self, pen : QtGui.QPen):
        self.pen = pen
    def change_color(self, color : QtGui.QColor):
        self.pen.setColor(color)
        self.brush.setColor(color)
    def set_brush(self, brush : QtGui.QBrush):
        self.brush = brush
    def change_style(self, style : Qtc.Qt.PenStyle):
        self.pen.setStyle(style)
    
    def draw_from_buffer(self, cached_pos):
        self._drawing = False #keep other events from interfering
        painter = QtGui.QPainter(self.whiteboard)
        painter.begin(self.whiteboard)
        for pos in cached_pos:
            painter.drawPoint(pos)
        painter.end()
        self.update()
        self._drawing = True
    #Overloaded Events
    def resizeEvent(self, event):
        # Recreate image when widget resizes
        if event.size() != self.whiteboard.size():
            new_image = QtGui.QImage(event.size(), QtGui.QImage.Format.Format_RGB32)
            new_image.fill(Qtc.Qt.GlobalColor.white)
            
            # Copy old drawing to new image
            painter = QtGui.QPainter(new_image)
            painter.drawImage(0, 0, self.whiteboard)
            
            self.whiteboard = new_image
        return super().resizeEvent(event)
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(self.rect(), self.whiteboard, self.whiteboard.rect())
    def mousePressEvent(self, event):
        if event.button() == Qtc.Qt.MouseButton.LeftButton:
            self._drawing = True
            self.last_pos = event.pos()
    def mouseMoveEvent(self, event):
        if self._drawing and event.buttons() & Qtc.Qt.MouseButton.LeftButton:
            # Draw on the image, not directly on widget
            self._point_log.append(self.last_pos)
            painter = QtGui.QPainter(self.whiteboard)
            painter.setPen(self.pen)
            painter.setBrush(self.brush)
            painter.drawLine(self.last_pos, event.pos())
            self.last_pos = event.pos()
            self.update()  # Triggers paintEvent
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qtc.Qt.MouseButton.LeftButton:
            self._drawing = False
            if self._point_log:
                self.new_drawing.emit(self._point_log.copy())
                self._point_log.clear()
    @Qtc.pyqtSlot()
    def penChanged(self):
        pass
    @Qtc.pyqtSlot(QtGui.QColor, name="color_change_event")
    def color_change_event(self, color):
        print("SLOT::Color changed to:", color.name())
        self.pen.setColor(color)
        self.brush.setColor(color)
        pass


