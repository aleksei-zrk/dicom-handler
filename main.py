from sorting import SortingByID, SortingByName
from glob import glob
import os
import re
import pydicom
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
from tkinter import Tk
from tkinter.filedialog import askdirectory


Tk().withdraw()
data_path = askdirectory()

#data_path = "/home/alex/PyDicom/DICOM"
output_path = working_path = "/home/alex/Documents/"
g = glob(data_path + '/*.dcm')

print("Total of %d DICOM images." % len(g))


#request_sort = input('Reallocate and sort DICOM files? Yes/No:')
""""
if request_sort == 'Yes':
    request_sort_method = input('Choose method of sorting: \n1. Name \n2. ID\n')

if request_sort_method == 'Name':
    SortingByName().sort()
elif request_sort_method == 'ID':
    SortingByID().sort()

"""
"""
subdirs = [re.sub(data_path, '', x[0]) for x in os.walk(data_path)]
del subdirs[0]
subdirs.sort()
print('\n'.join(subdirs))
"""
#data_to_proceed = input('Choose patient to work with:')

def load_scan(path):
    slices = [pydicom.dcmread(path + '/' + s)
              for s in os.listdir(path)]
    slices.sort(key=lambda x: int(x.InstanceNumber))
    try:
        slice_thickness = np.abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
    except:
        slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)

    for s in slices:
        s.SliceThickness = slice_thickness

    return slices

def get_pixels_hu(scans):
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
    #image[np.logical_and(image >= -400, image < 400)] = -1000

    return np.array(image, dtype=np.int16)


id = 0
Tk().withdraw()
data_path1 = askdirectory()
print(data_path1)
patient = load_scan(data_path1)
imgs = get_pixels_hu(patient)

np.save(output_path + "fullimages_%d.npy" % (id), imgs)

file_used = output_path + "fullimages_%d.npy" % id
imgs_to_process = np.load(file_used).astype(np.float64)

plt.hist(imgs_to_process.flatten(), bins=50, color='c')
plt.xlabel("Hounsfield Units (HU)")
plt.ylabel("Frequency")
plt.show()


id = 0
imgs_to_process = np.load(output_path+'fullimages_{}.npy'.format(id))

def sample_stack(stack, rows=9, cols=9, start_with=0, show_every=1):
    fig, ax = plt.subplots(rows, cols, figsize=[20,20])
    plt.subplots_adjust(hspace=0.43)
    for i in range(rows*cols):
        ind = start_with + i*show_every
        ax[int(i/rows),int(i % rows)].set_title('Срез {}'.format(ind), fontsize=7)
        ax[int(i/rows),int(i % rows)].imshow(stack[ind],cmap='gray')
        ax[int(i/rows),int(i % rows)].axis('off')
    plt.show()

sample_stack(imgs_to_process)
image3 = imgs_to_process[25]
#image3[np.logical_and(image3 >= -400, image3 < 300)] = -1000
#plt.imshow(image3, cmap='gray', interpolation='bilinear')
#
plt.imshow(image3, cmap='gray', interpolation='bilinear')
plt.show()


el = scipy.ndimage.grey_dilation(image3, size=(3, 3))
plt.imshow(el, cmap='gray', interpolation='bilinear')
plt.show()

"""
plt.contour(image3, [-1500, -800], colors='brown', linestyles='solid')#air
plt.contour(image3, [-550, -450], colors='blue', linestyles='solid')#lungs
plt.contour(image3, [250, 3000], colors='cyan', linestyles='solid')#bones
plt.contour(image3, [-120, -90], colors='yellow', linestyles='solid')#fat
plt.contour(image3, [10, 40], colors='red', linestyles='solid')#muscles
plt.legend(['something'])
plt.show()

"""