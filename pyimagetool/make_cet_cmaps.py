import os
import numpy as np

names = {
    'CET-L1': 'CET-L-Gry',
    'CET-L4': 'CET-L-Red-Yel',
    'CET-L5': 'CET-L-Blk-Grn-Yel',
    'CET-L6': 'CET-L-Blk-Blu-Cyn',
    'CET-L13': 'CET-L-Red',
    'CET-L14': 'CET-L-Grn',
    'CET-L15': 'CET-L-Blu',
    'CET-D1A': 'CET-D-Blu-Wht-Red',
    'CET-D4': 'CET-D-Blu-Blk-Red',
    'CET-D13': 'CET-D-Blu-Wht-Grn',
    'CET-R2': 'CET-R-Blu-Grn-Yel-Red',
    'CET-C2': 'CET-C-Mrn-Yel-Grn-Blu',
    'CET-C4': 'CET-C-Red-Wht-Blu',
    'CET-C5': 'CET-C-Gry'
         }

for dirName, subdirList, fileList in os.walk('.'):
    if dirName == '.' + os.sep + 'CETperceptual_csv_0_255':
        for filename in fileList:
            kwd = filename[:-4]
            if kwd in names.keys():
                dat = np.loadtxt(dirName + os.sep + filename, dtype=np.uint8, delimiter=',')
                newname = os.path.splitext('.' + os.sep + 'cmaps' + os.sep + names[kwd])[0]
                print(newname)
                np.save(newname, dat)
