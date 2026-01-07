import PyQt6.QtGui as QtGui
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
for i in range(16):
    color = QtGui.QColor.fromHsv(i * 22, 255, 255)
    COLOR_OPTIONS.append(color)

for qcolor in COLOR_OPTIONS:
    print(qcolor.name())