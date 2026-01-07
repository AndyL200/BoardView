import json
import os
from dump import Dump, DUMP_DIR, LOCAL_DIR, CATALOG_PATH
import threading
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class Scraper:
    _catalog = {}
    def __init__(self, search=None):
        if search:
            self.setCatalogPartial(search)
        else:
            self.setCatalogFull()
        pass
    def catalog(self):
        return self._catalog
    def setCatalogFull(self):
        path = os.path.join(os.path.dirname(__file__), '../local', 'catalog.json')
        _catalog = json.load(open(path, 'r', encoding='utf-8'))
        self._catalog = _catalog
    def setCatalogPartial(self, search):
        self.setCatalogFull()
        new_catalog = []
        for item in self._catalog:
            #need a better search algorithm later
            if search.lower() in item['identifier'].lower():
                new_catalog.append(item)
        self._catalog = new_catalog
    def setCatalogEmpty(self):
        pass
    #future
    def setCatalogOutsource(self):
        pass
class ScraperLight():
    _catalog = {}
    def __init__(self):
        self.indexImages()

    def indexImages(self):
        _catalog = json.load(open(CATALOG_PATH, 'r', encoding='utf-8'))
        self._catalog = _catalog
    def getLength(self):
        return len(self._catalog)
    def grab_catalog_range(self, start, end):
        return self._catalog[start:end]

class DumpHandler(FileSystemEventHandler):
    #Override
    def on_created(self, event):
        print(f"New file detected: {event.src_path}")
        if not event.is_directory:
            dumper = Dump()
            dumper.parseDump()
class FileListener:
    def __init__(self):
        os.makedirs(DUMP_DIR, exist_ok=True)
        os.makedirs(LOCAL_DIR, exist_ok=True)
        self.watch_path = DUMP_DIR
        self.observer = Observer()
        self.observer.schedule(DumpHandler(), self.watch_path, recursive=True)
    def start(self):
        self.observer.start()
        print(f"Listening for files in {self.watch_path}...")
    
    def stop(self):
        self.observer.stop()
        self.observer.join()

listener = FileListener()
listener.start()
