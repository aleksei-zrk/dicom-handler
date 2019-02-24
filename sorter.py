import os
from glob import glob
from abc import ABCMeta, abstractmethod
from shutil import copyfile
import re

import pydicom


class Sorter(metaclass=ABCMeta):
    @abstractmethod
    def sort(self, path):
        pass


class SorterByID(Sorter):

    def sort(self, path):
        g = glob(path + '/*.dcm')
        for file in g:
            try:
                pydicom.dcmread(file).SliceLocation
            except AttributeError:
                continue
            id = pydicom.dcmread(file).PatientID
            instance = pydicom.dcmread(file).InstanceNumber
            try:
                os.makedirs(path + '/{}'.format(id))
            except:
                pass
            copyfile(file, path+'/{}/{}.dcm'.format(id, instance))


class SorterByName(Sorter):

    def sort(self, path):
        g = glob(path + '/*.dcm')
        for file in g:
            try:
                pydicom.dcmread(file).SliceLocation
            except AttributeError:
                continue
            name = str(pydicom.dcmread(file).PatientName)
            name = re.sub(r'[-/\d\']', '', name)
            name = name.strip()
            instance = pydicom.dcmread(file).InstanceNumber
            try:
                os.makedirs(path + '/{}'.format(name))
            except:
                pass
            copyfile(file, path+'/{}/{}.dcm'.format(name, instance))


