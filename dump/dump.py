import os
import json
import cv2
import shutil
from ultralytics import YOLO
#import some AI element to identify image content


class Dump:
    def __init__(self):
        self._model = YOLO("yolo11n.pt")  # load a pretrained model
        self._model.train(data='coco8.yaml', epochs=15)
        pass
    def parseDump(self):
        for file in os.listdir(os.curdir):
            if not (file.endswith('py') or file.endswith('json')):
                file_path = os.path.join(os.curdir, file)
                img = cv2.imread(file_path)
                predict = self._model(img, save=False)
                print(predict)
                #save to catalog
                with open(os.path.join('origin', 'local', 'catalog.json'), 'a', encoding='utf-8') as catalog:
                    d = json.dump({
                                'file_name': file,
                                'file_url': file_path,
                                'identifier': str(predict)
                            })
                    catalog.write(d)
                    #move file to local
                shutil.move(file_path, os.path.join('origin', 'local', file))