import os
import json
import cv2
import shutil
from ultralytics import YOLO
#import some AI element to identify image content

DUMP_DIR = os.path.join('origin', 'dump')
LOCAL_DIR = os.path.join('origin', 'local')
CATALOG_PATH = os.path.join(LOCAL_DIR, 'catalog.json')
PREV_MODEL_PATH = os.path.join("runs", "detect", "train", "weights", "best.pt")

class Dump:
    def __init__(self):
        #make json if not exists
        if not os.path.exists(CATALOG_PATH):
            with open(CATALOG_PATH, 'w', encoding='utf-8') as catalog_file:
                json.dump([], catalog_file)
        if os.path.exists(PREV_MODEL_PATH): #if trained model exists
            self._model = YOLO(PREV_MODEL_PATH)
        else:
            self._model = YOLO("yolo11n.pt")  # load a pretrained model
            self._model.train(data='coco8.yaml', epochs=15)
    def parseDump(self):
        if not self.dumpActive():
            return
        print("Parsing dump folder...")
        catalog = self.loadCatalog()
        for file in os.listdir( os.path.join('origin', 'dump')):
            if not (file.lower().endswith(('png', 'jpeg', 'jpg'))):
                continue
            file_path = os.path.join(DUMP_DIR, file)
            img = cv2.imread(file_path)
            predict = self._model.predict(img, save=False)
            print(predict)
            #save to catalog
            catalog.append(
                {
                    "file_name": file,
                    "file_url": os.path.join(LOCAL_DIR, file),
                    "identifier": str(sorted(predict[0].probs)) if predict[0].probs is not None else "unidentified",
                }
            )
                #move file to local
            shutil.move(file_path, os.path.join(LOCAL_DIR, file))
        with open(CATALOG_PATH, 'w', encoding='utf-8') as catalog_file:
            json.dump(catalog, catalog_file, indent=4)
    def loadCatalog(self):
        if os.path.exists(CATALOG_PATH):
            with open(CATALOG_PATH, 'r', encoding='utf-8') as catalog:
                try:
                    return json.load(catalog)
                except json.JSONDecodeError:
                    print("Decode error")
                    return []
        return []

    def dumpActive(self):
        
        return len(os.listdir(DUMP_DIR)) > 0 and os.path.exists(LOCAL_DIR) and os.path.exists(DUMP_DIR)