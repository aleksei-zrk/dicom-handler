import re
from datetime import datetime
from glob import glob

import pydicom


class Patient(object):
    def __init__(self, path):
        self.file = pydicom.dcmread(glob(path + '/*.dcm')[0])
        self.name = self.file.PatientName
        self.id = self.file.PatientID
        self.birthday = self.file.PatientBirthDate
        self.sex = self.file.PatientSex
        self.body_part = self.file.BodyPartExamined
        self.study_date = self.file.StudyDate

    def get_name(self):
        name = re.sub(r'[-/\d\']', '', str(self.name))
        name = name.strip()
        return name

    def get_id(self):
        return self.id

    def get_birth_date(self):
        return str(datetime.strptime(self.birthday, '%Y%m%d').date())

    def get_study_date(self):
        return str(datetime.strptime(self.study_date, '%Y%m%d').date())

    def get_sex(self):
        if str(self.sex) == 'F':
            return 'Female'
        else:
            return 'Male'

    def get_body_part(self):
        return self.body_part



