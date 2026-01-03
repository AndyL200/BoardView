import json
import os
from dump import Dump
import threading
#open dump on startup

def OpenDump():
    dump = Dump()
    dump.parseDump()

#Allow dump to run as needed with a listener
def ThreadTimer():
    #listen for new files every minute
    dump_listener = threading.Timer(60.0, ThreadTimer)
    dump_listener.start()

class Scraper:
    _catalog = []
    def __init__(self, search=None):
        if search:
            self.setCatalogPartial(search)
        else:
            self.setCatalogFull()
        pass
    def catalog(self):
        return self._catalog
    def setCatalogFull(self):
        path = os.path.join('origin', 'local')
        if os.path.exists(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    self._catalog.append({
                        'file_name': file,
                        'identifier': '',
                        'file_url': file_path
                    })
    def setCatalogPartial(self, search):
        self.setCatalogFull()
        new_catalog = []
        for item in self._catalog:
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
        _catalog = json.load(open(os.path.join('origin', 'local', 'catalog.json'), 'r', encoding='utf-8'))
        self._catalog = _catalog
    def getLength(self):
        return len(self._catalog)
    def grab_catalog_range(self, start, end):
        return self._catalog[start:end]
    
print(os.path.exists(os.path.join('origin', 'local')))