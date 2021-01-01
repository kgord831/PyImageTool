import os
from xml.dom import minidom
import numpy as np

names = {
    'mellow-rainbow': 'mellow_rainbow',
    'gr-insert_40-50': 'highlight',
    'gr-insert_40-60': 'highlight_2',
    'blue-orange-div': 'blue_orange'
         }

for dirName, subdirList, fileList in os.walk('.'):
    if dirName == '.' + os.sep + 'scivis_cmaps':
        for filename in fileList:
            kwd = filename[:-4]
            if kwd in names.keys():
                xmldoc = minidom.parse(dirName + os.sep + filename)
                pts = xmldoc.getElementsByTagName('Point')
                x_pnts = np.empty(len(pts))
                read_pnts = np.empty((len(pts), 3))
                for i, pt in enumerate(pts):
                    x_pnts[i] = float(pt.attributes['x'].value)
                    r = float(pt.attributes['r'].value)
                    g = float(pt.attributes['g'].value)
                    b = float(pt.attributes['b'].value)
                    read_pnts[i, 0] = r
                    read_pnts[i, 1] = g
                    read_pnts[i, 2] = b
                dat = np.empty((256, 3), dtype=np.uint8)
                print(np.round(255*np.interp(np.arange(256) / 255, x_pnts, read_pnts[:, 0])).astype(np.uint8))
                dat[:, 0] = np.round(255*np.interp(np.arange(256) / 255, x_pnts, read_pnts[:, 0])).astype(np.uint8)
                dat[:, 1] = np.round(255*np.interp(np.arange(256) / 255, x_pnts, read_pnts[:, 1])).astype(np.uint8)
                dat[:, 2] = np.round(255*np.interp(np.arange(256) / 255, x_pnts, read_pnts[:, 2])).astype(np.uint8)
                newname = os.path.splitext('.' + os.sep + 'cmaps' + os.sep + names[kwd])[0]
                print(newname)
                np.save(newname, dat)
