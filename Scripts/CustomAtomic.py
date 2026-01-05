
import PyQt6.QtWidgets as Qtw
from threading import Lock

class AtomicInteger:
    def __init__(self, initial=0):
        self.value = initial
        self.lock = Lock()
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
        
class AtomicClockVLayout(Qtw.QVBoxLayout):
    atom_count = AtomicInteger()
    def __init__(self, master):
        super().__init__(master)