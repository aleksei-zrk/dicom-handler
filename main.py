import os
import re
import math
import json
import sqlite3

from glob import glob
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import scipy.ndimage
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.filedialog import askdirectory
import pony.orm
from pony.orm.core import IntegrityError
from terminaltables import AsciiTable

from sorter import SorterByID, SorterByName
from handler import ScanReader, sample_stack
from classes import Patient
import db_template

def format_dict(d):

    d = json.dumps(d, indent=0, ensure_ascii=False)
    d = re.sub(r'["}{,]', '', d)
    return d

@db_template.db_session
def show_database():

    def close():
        root.quit()
        root.destroy()

    root = tk.Toplevel()
    root.configure(bg='white')
    try:
        db_template.db.bind(provider='sqlite', filename='patients.sqlite', create_db=True)
        db_template.db.generate_mapping(check_tables=True)
    except:
        pass
    data = db_template.db.select('select * from PatientData')
    data = [('ID', 'Name', 'Sex', 'Body part')] + data
    table = AsciiTable(data, title='Patient database')
    root.title('Patient Database')
    tk.Label(root, text=table.table, background='white').pack()
    tk.Button(root, text='OK', command=lambda: close(), bg='white').pack()
    root.mainloop()


def sort():
    tk.Tk().withdraw()
    data_path = askdirectory()
    global output_path, working_path, g
    output_path = working_path = "/home/alex/Documents/"
    g = glob(data_path + '/*.dcm')

    messagebox.showinfo('Message', 'Total of {} DICOM images.'.format(len(g)))

    answer = messagebox.askyesno('', 'Reallocate and sort DICOM files?')


    if answer:
        root = tk.Tk()

        def method_choose(choice):
            if choice == 'Name':
                SorterByName().sort(data_path)
            else:
                SorterByID().sort(data_path)

            root.quit()


        tk.Label(root, text='Choose method of sorting:', justify=tk.LEFT, padx=20).pack()
        tk.Button(root, text='Name', padx=20, command=lambda: method_choose('Name')).pack(anchor=tk.W)
        tk.Button(root, text='ID', padx=20, command=lambda: method_choose('ID')).pack(anchor=tk.W)
        #tk.Button(root, text='OK', compound=tk.RIGHT, command=root.quit).pack()
        root.mainloop()
        root.destroy()



root = tk.Tk()
menubar = tk.Menu(root)
root.title('Menu')
menubar.add_command(label='Show Patient database', command=lambda: show_database())
menubar.add_command(label='Reallocate and sort DICOM', command=lambda: sort())

root.config(menu=menubar)
root.mainloop()





reader = ScanReader()

id = 0
#tk.Tk().withdraw()
patient_path = askdirectory()
print(patient_path)

patient = Patient(patient_path)

patient_params = {'Patient ID': patient.get_id(),
                  'Patient Name': patient.get_name(),
                  'Patient Sex': patient.get_sex(),
                  'Body part examined': patient.get_body_part()}

root = tk.Tk()



root.title('Patient Parameters')
tk.Label(root, text='Patient parameters are:\n {}'.format(format_dict(patient_params)), font=('Arial', 16)).pack()
tk.Button(root, text='OK', compound=tk.RIGHT, command=root.quit).pack()
root.mainloop()
root.destroy()

if messagebox.askyesno('Database', 'Enter patient to the database?'):

    try:
        db_template.db.bind(provider='sqlite', filename='patients.sqlite', create_db=True)
        db_template.db.generate_mapping(create_tables=True)
    except:
        pass
    @db_template.db_session
    def enter_patient(id, name, sex, body_part):
        db_template.PatientData(id=id, name=name, sex=sex, body_part=body_part)

    try:
        enter_patient(patient_params['Patient ID'],
                      patient_params['Patient Name'],
                      patient_params['Patient Sex'],
                      patient_params['Body part examined'])
    except:
        print('Patient already in the database')
        pass



patient_scans = reader.load_scan(patient_path)
imgs = reader.get_pixels_hu(patient_scans)

np.save(output_path + "fullimages_%d.npy" % (id), imgs)

file_used = output_path + "fullimages_%d.npy" % id



id = patient_params['Patient ID']
imgs_to_process = np.load(output_path+'fullimages_{}.npy'.format(id))
print(len(imgs_to_process))


if messagebox.askyesno('Save images', 'Slices loaded!\nSave slices as images?'):
    i = 0
    try:
        os.mkdir(patient_path + '/imgs/')
    except FileExistsError:
        pass
    for image in imgs_to_process:
        i += 1
        plt.imshow(image, cmap='gray', interpolation='bilinear')
        plt.savefig(patient_path + '/imgs/image_{}.jpg'.format(i), bbox_inches=None)



#sample_stack(imgs_to_process)
answer = simpledialog.askinteger('Input', 'Choose slice:', parent=sample_stack(imgs_to_process))
image3 = imgs_to_process[answer]
#image3[np.logical_and(image3 >= -400, image3 < 300)] = -1000
#plt.imshow(image3, cmap='gray', interpolation='bilinear')
#
plt.imshow(image3, cmap='gray', interpolation='bilinear')
plt.show()


el = scipy.ndimage.grey_dilation(image3, size=(3, 3))

plt.imshow(el, cmap='gray', interpolation='bilinear')
plt.show()



med = scipy.ndimage.median_filter(image3, 7)
plt.imshow(med, cmap='gray', interpolation='bilinear')
plt.show()




image3 = med
plt.imshow(image3, cmap='gray', interpolation='bilinear')
plt.contour(image3, [-1500, -800], colors='brown', linestyles='solid')#air
plt.contour(image3, [-550, -450], colors='blue', linestyles='solid')#lungs
plt.contour(image3, [250, 3000], colors='cyan', linestyles='solid')#bones
plt.contour(image3, [-170, -45], colors='yellow', linestyles='solid')#fat
plt.contour(image3, [10, 105], colors='red', linestyles='solid')#muscles
plt.axis('off')
plt.savefig('contoured.jpg', bbox_inches=None)
plt.show()