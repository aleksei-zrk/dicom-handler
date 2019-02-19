import pydicom
import numpy as np
import os
import math
import matplotlib.pyplot as plt
from abc import ABCMeta, abstractmethod


class ScanReader(object):

    def load_scan(self, path):

        slices = [pydicom.dcmread(path + '/' + s)
                  for s in sorted(os.listdir(path)) if os.path.isfile(os.path.join(path, s))]
        slices.sort(key=lambda x: int(x.InstanceNumber))
        try:
            slice_thickness = np.abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
        except:
            slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)

        for s in slices:
            s.SliceThickness = slice_thickness

        return slices

    def get_pixels_hu(self, scans):
        image = np.stack([s.pixel_array for s in scans])
        # Convert to int16 (from sometimes int16),
        # should be possible as values should always be low enough (<32k)
        image = image.astype(np.int16)

        # Set outside-of-scan pixels to 1
        # The intercept is usually -1024, so air is approximately 0
        image[image == -2000] = 0

        # Convert to Hounsfield units (HU)
        intercept = scans[0].RescaleIntercept
        slope = scans[0].RescaleSlope

        if slope != 1:
            image = slope * image.astype(np.float64)
            image = image.astype(np.int16)

        image += np.int16(intercept)
        # image[np.logical_and(image >= -400, image < 400)] = -1000

        return np.array(image, dtype=np.int16)


def sample_stack(stack, rows=None, cols=None, start_with=0, show_every=1):
    if round(math.sqrt(len(stack))) ** 2 >= len(stack):
        rows = cols = int(math.sqrt(len(stack)))
    else:
        rows = round(math.sqrt(len(stack)))
        cols = rows + 1

    fig, ax = plt.subplots(rows, cols, figsize=[20,20])
    plt.subplots_adjust(top=0.965, bottom=0, left=0, right=1, hspace=0.43)
    plt.title('Choose slice to handle:')
    #Button(plt.close('all'), 'close')
    for i in range(rows*cols):
        ind = start_with + i*show_every
        ax[int(i/rows),int(i % rows)].set_title('Срез {}'.format(ind), fontsize=7)
        ax[int(i/rows),int(i % rows)].imshow(stack[ind],cmap='gray')
        ax[int(i/rows),int(i % rows)].axis('off')
    plt.show()


class ImgSaver(object):
    pass


class Contourer(metaclass=ABCMeta):
    pass

class ContourerChest(Contourer):
    pass