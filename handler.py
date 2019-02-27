import os
import math
from abc import ABCMeta, abstractmethod

import pydicom
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
from skimage import measure
from plotly import figure_factory as FF
from plotly.offline import plot, init_notebook_mode


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

        image = image.astype(np.int16)

        image[image == -2000] = 0

        # Convert to Hounsfield units (HU)
        intercept = scans[0].RescaleIntercept
        slope = scans[0].RescaleSlope

        if slope != 1:
            image = slope * image.astype(np.float64)
            image = image.astype(np.int16)

        image += np.int16(intercept)

        return np.array(image, dtype=np.int16)


def sample_stack(stack, start_with=0, show_every=1):
    if round(math.sqrt(len(stack))) ** 2 >= len(stack):
        rows = cols = int(math.sqrt(len(stack)))
    else:
        rows = round(math.sqrt(len(stack)))
        cols = rows
    # Creates table of subplots with slices
    fig, ax = plt.subplots(rows, cols, figsize=[20,20])
    plt.subplots_adjust(top=0.965, bottom=0, left=0, right=1, hspace=0.43)
    plt.title('Choose slice to handle:')

    for i in range(rows*cols):
        ind = start_with + i*show_every
        ax[int(i/rows),int(i % rows)].set_title('Срез {}'.format(ind), fontsize=7)
        ax[int(i/rows),int(i % rows)].imshow(stack[ind],cmap='gray')
        ax[int(i/rows),int(i % rows)].axis('off')
    plt.show()


class Contourer(metaclass=ABCMeta):

    @abstractmethod
    def contour(self, image, path, save, id):
        pass


class ContourerNeck(Contourer):

    def contour(self, image, path=None, save=True, id=0):
        image = scipy.ndimage.median_filter(image, 4)
        plt.imshow(image, cmap='gray')
        plt.contour(image, [-1500, -800], colors='blue', linestyles='solid')  # air
        plt.contour(image, [-550, -450], colors='brown', linestyles='solid') # lungs
        plt.contour(image, [250, 3000], colors='cyan', linestyles='solid')  # bones
        plt.contour(image, [-170, -45], colors='yellow', linestyles='solid')  # fat
        plt.contour(image, [10, 105], colors='red', linestyles='solid')  # muscles

        if save:
            plt.savefig(path + '/contoured_{}.jpg'.format(id), bbox_inches=None)
        else:
            plt.show()

        plt.clf()


class ContourerChest(Contourer):

    def contour(self, image, path=None, save=True, id=0):
        image = scipy.ndimage.median_filter(image, 3)
        plt.imshow(image, cmap='gray')
        plt.contour(image, [-1500, -800], colors='blue', linestyles='solid')  # air
        plt.contour(image, [-550, -450], colors='brown', linestyles='solid')  # lungs
        plt.contour(image, [250, 3000], colors='cyan', linestyles='solid')  # bones
        plt.contour(image, [-170, -45], colors='yellow', linestyles='solid')  # fat
        plt.contour(image, [10, 105], colors='red', linestyles='solid')  # muscles

        if save:
            plt.savefig(path + '/contoured_{}.jpg'.format(id), bbox_inches=None)
        else:
            plt.show()

        plt.clf()

class ContourerPelvis(Contourer):

    def contour(self, image, path=None, save=True, id=0):
        image = scipy.ndimage.median_filter(image, 5)
        plt.imshow(image, cmap='gray')
        plt.contour(image, [-1500, -800], colors='blue', linestyles='solid')  # air
        plt.contour(image, [250, 3000], colors='cyan', linestyles='solid')  # bones
        plt.contour(image, [-170, -45], colors='yellow', linestyles='solid')  # fat
        plt.contour(image, [10, 105], colors='red', linestyles='solid')  # muscles

        if save:
            plt.savefig(path + '/contoured_{}.jpg'.format(id), bbox_inches=None)
        else:
            plt.show()

        plt.clf()


class Plot3D(object):

    def resample(self, image, scan, new_spacing=[1, 1, 1]):
        # Determine current pixel spacing
        spacing = list(scan[0].PixelSpacing)
        spacing.insert(0, scan[0].SliceThickness)

        spacing = map(float, spacing)
        spacing = np.array(list(spacing))

        resize_factor = spacing / new_spacing
        new_real_shape = image.shape * resize_factor
        new_shape = np.round(new_real_shape)
        real_resize_factor = new_shape / image.shape
        new_spacing = spacing / real_resize_factor

        image = scipy.ndimage.interpolation.zoom(image, real_resize_factor)

        return image, new_spacing

    def make_mesh(self, image, threshold=-300, step_size=1):
        # Creates surface
        p = image.transpose(2, 1, 0)

        verts, faces, norm, val = measure.marching_cubes_lewiner(p, threshold, step_size=step_size, allow_degenerate=True)
        return verts, faces

    def plotly_3d(self, verts, faces, path, filename):
        init_notebook_mode(connected=True)

        x, y, z = zip(*verts)

        colormap = ['rgb(236, 236, 212)', 'rgb(236, 236, 212)']

        fig = FF.create_trisurf(x=x,
                                y=y,
                                z=z,
                                plot_edges=False,
                                colormap=colormap,
                                simplices=faces,
                                backgroundcolor='rgb(64, 64, 64)',
                                title="Interactive Visualization")
        plot(fig, filename=path + '/3D_' + filename +'.html')
