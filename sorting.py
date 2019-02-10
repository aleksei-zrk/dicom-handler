import pydicom
import os
from glob import glob
from abc import ABCMeta, abstractmethod
from shutil import copyfile
import re

data_path = "/home/alex/PyDicom/DICOM"
g = glob(data_path + '/*.dcm')

class Sorting(metaclass=ABCMeta):
    @abstractmethod
    def sort(self):
        pass


class SortingByID(Sorting):

    def sort(self):
        for file in g:
            id = pydicom.dcmread(file).PatientID
            instance = pydicom.dcmread(file).InstanceNumber
            try:
                os.makedirs(data_path + '/{}'.format(id))
            except:
                pass
            copyfile(file, data_path+'/{}/{}.dcm'.format(id, instance))

class SortingByName(Sorting):

    def sort(self):
        for file in g:
            name = str(pydicom.dcmread(file).PatientName)
            name = re.sub(r'[-/\d\']', '', name)
            name = name.strip()
            instance = pydicom.dcmread(file).InstanceNumber
            try:
                os.makedirs(data_path + '/{}'.format(name))
            except:
                pass
            copyfile(file, data_path+'/{}/{}.dcm'.format(name, instance))


sort_name = SortingByID()
sort_name.sort()

