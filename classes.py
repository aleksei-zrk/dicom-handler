from glob import glob
import pydicom

class Patient(object):
    def __init__(self, path):
        self.file = pydicom.dcmread(glob(path + '/*.dcm')[0])
        self.name = self.file.PatientName
        self.id = self.file.PatientID
        self.sex = self.file.PatientSex
        self.body_part = self.file.BodyPartExamined

    def get_name(self):
        return self.name

    def get_id(self):
        return self.id

    def get_sex(self):
        return self.sex

    def get_body_part(self):
        return self.body_part



