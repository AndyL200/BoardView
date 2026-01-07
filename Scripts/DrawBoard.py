import PyQt6.QtWidgets as Qtw
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as Qtc

class DrawingBoard(Qtw.QWidget):
    new_drawing = Qtc.pyqtSignal(list, name="send_board_data")  #Signal emitted when new drawing data is available

    pen : QtGui.QPen
    brush : QtGui.QBrush

    

    #Note: A Pen is used for outlines while a Brush is used for filling shapes
    def __init__(self, master):
        super().__init__(master)

        self._line_log : list = []  #Cache of points drawn since last update
        self._pending : bool = False
        self._pending_draws : list = []
        self._drawing : bool = False #mutex or lock? #Lock while drawing in progress

        self.master = master
        
        self.whiteboard = QtGui.QImage(self.size(), QtGui.QImage.Format.Format_RGB32)
        self.whiteboard.fill(Qtc.Qt.GlobalColor.white)

        
        self.brush = QtGui.QBrush(Qtc.Qt.GlobalColor.black)
        self.pen = QtGui.QPen(Qtc.Qt.GlobalColor.black, 3, Qtc.Qt.PenStyle.SolidLine, Qtc.Qt.PenCapStyle.RoundCap, Qtc.Qt.PenJoinStyle.RoundJoin)

        self._drawing = False
        self.last_pos = (0,0)

        
        
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
    
    @Qtc.pyqtSlot(list)
    def draw_from_buffer(self, cached_pos):
        self._pending_draws = cached_pos.copy() if cached_pos else []
        if len(self._pending_draws) > 0:
            self._pending = True
        self.update()  # Triggers paintEvent

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
        painter.end()

        if self._pending:
            
            painter = QtGui.QPainter(self.whiteboard)
            
            
            painter.setPen(self.pen)
            painter.setBrush(self.brush) #last two are PEN and BRUSH
            print("Drawing from buffer with", len(self._pending_draws), "points.")
            
            for i in range(len(self._pending_draws)):
                if "PEN" in self._pending_draws[i]:
                    if len(self._pending_draws[i]["PEN"]) != 5:
                        print("Invalid PEN data:", self._pending_draws[i]["PEN"])
                    pen_data = QtGui.QPen(QtGui.QColor(self._pending_draws[i]["PEN"][0]), self._pending_draws[i]["PEN"][1], Qtc.Qt.PenStyle(self._pending_draws[i]["PEN"][2]), Qtc.Qt.PenCapStyle(self._pending_draws[i]["PEN"][3]), Qtc.Qt.PenJoinStyle(self._pending_draws[i]["PEN"][4]))
                    painter.setPen(pen_data)
                    continue
                if "BRUSH" in self._pending_draws[i]:
                    try:
                        brush_data = QtGui.QBrush(QtGui.QColor(self._pending_draws[i]["BRUSH"]))
                        painter.setBrush(brush_data)
                    except:
                        print("Invalid BRUSH data:", self._pending_draws[i]["BRUSH"])
                if "LOG" in self._pending_draws[i]:
                    try:
                        for line in self._pending_draws[i]["LOG"]:
                            if len(line) != 4:
                                print("Invalid line data:", line)
                                continue
                            painter.drawLine(line[0], line[1], line[2], line[3])
                    except:
                        print("Invalid IMG data")
            painter.end()
            self._pending_draws.clear()
            self._pending = False
            
    def mousePressEvent(self, event):
        if event.button() == Qtc.Qt.MouseButton.LeftButton:
            self._drawing = True
            self.last_pos = (event.pos().x(), event.pos().y())
    def mouseMoveEvent(self, event):
        if self._drawing and event.buttons() & Qtc.Qt.MouseButton.LeftButton:
            # Draw on the image, not directly on widget
            
            painter = QtGui.QPainter(self.whiteboard)
            painter.setPen(self.pen)
            painter.setBrush(self.brush)
            painter.drawLine(self.last_pos[0], self.last_pos[1], event.pos().x(), event.pos().y())
            self._line_log.append([self.last_pos[0], self.last_pos[1], event.pos().x(), event.pos().y()]) #Log the line drawn
            self.last_pos = (event.pos().x(), event.pos().y())
            painter.end()
            self.update()  # Triggers paintEvent
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qtc.Qt.MouseButton.LeftButton:
            self._drawing = False
            if self._line_log:
                print("Emitting new drawing signal with", len(self._line_log), "points.")
                # img_byte_array = Qtc.QByteArray()
                # iodev = Qtc.QBuffer(img_byte_array)
                # iodev.open(Qtc.QIODevice.OpenModeFlag.WriteOnly)
                # self.whiteboard.save(iodev, "PNG")
                # iodev.close()
                #send whole image vs send lines only?
                
                buffer_data = [{"PEN": [self.pen.color().name(), self.pen.width(), int(self.pen.style().value), int(self.pen.capStyle().value), int(self.pen.joinStyle().value)], "BRUSH": self.brush.color().name(), "LOG": self._line_log.copy()}]
                self.new_drawing.emit(buffer_data)
                self._line_log.clear()
    @Qtc.pyqtSlot()
    def penChanged(self):
        pass
    @Qtc.pyqtSlot(QtGui.QColor, name="color_change_event")
    def color_change_event(self, color):
        print("SLOT::Color changed to:", color.name())
        self.pen.setColor(color)
        self.brush.setColor(color)
        pass


