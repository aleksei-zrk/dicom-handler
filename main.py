import os
import re
import json
import getpass
from glob import glob

import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.filedialog import askdirectory
from terminaltables import AsciiTable

import db_template
from sorter import SorterByID, SorterByName
from handler import ScanReader, sample_stack, ContourerNeck, ContourerChest, ContourerPelvis
from classes import Patient


class BodyPartError(Exception):
    pass

output_path = working_path = '/home/{}/Documents/'.format(getpass.getuser())

def format_dict(d):
    d = json.dumps(d, indent=0, ensure_ascii=False)
    d = re.sub(r'["}{,]', '', d)
    return d


@db_template.db_session
def show_database():

    def close():
        root.destroy()

    def delete(id):
        db_template.db.select('delete {} from PatientData'.format(id))

    try:
        db_template.db.bind(provider='sqlite', filename='patients.sqlite', create_db=True)
        db_template.db.generate_mapping(check_tables=True)
    except:
        pass
    try:
        data = db_template.db.select('select * from PatientData')
    except:
        popup = tk.Toplevel()
        popup.title('Info')
        tk.Label(master=popup, text='There is no database!', font='Arial, 10').pack()
        tk.Button(master=popup, text='OK', command=lambda: popup.destroy()).pack()
        return
    data = [('ID', 'Name', 'Sex', 'Birth Date', 'Body part')] + data
    table = AsciiTable(data, title='Patient database')
    root = tk.Toplevel()
    root.configure(bg='white')
    root.title('Patient Database')
    tk.Label(root, text=table.table, background='white').pack()
    tk.Button(root, text='OK', command=lambda: close(), bg='white').pack()
    tk.Button(root, text='Delete ', command=lambda: close(), bg='white').pack()
    root.mainloop()


def sort():
    tk.Tk().withdraw()
    data_path = askdirectory()
    global working_path, g

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
        tk.Button(root, text='Name', padx=20, command=lambda: method_choose('Name')).pack(anchor=tk.N)
        tk.Button(root, text='ID', padx=20, command=lambda: method_choose('ID')).pack(anchor=tk.N)
        root.mainloop()
        root.destroy()

def patient_load():
    reader = ScanReader()

    patient_path = askdirectory()

    patient = Patient(patient_path)

    patient_params = {'Patient ID': patient.get_id(),
                      'Patient Name': patient.get_name(),
                      'Patient Sex': patient.get_sex(),
                      'Birth Date': patient.get_birth_date(),
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
        def enter_patient(id, name, sex, birthday, body_part):

            db_template.PatientData(id=id, name=name, sex=sex, birthday=birthday, body_part=body_part)

        enter_patient(patient_params['Patient ID'],
                      patient_params['Patient Name'],
                      patient_params['Patient Sex'],
                      patient_params['Birth Date'],
                      patient_params['Body part examined'])


    patient_scans = reader.load_scan(patient_path)
    imgs = reader.get_pixels_hu(patient_scans)

    id = patient_params['Patient ID']
    name = patient_params['Patient Name']
    body_part = patient_params['Body part examined']
    np.save(output_path + "fullimages_{}({}, {}).npy".format(id, name, body_part), imgs)

    imgs = np.load(output_path + 'fullimages_{}({}, {}).npy'.format(id, name, body_part))

    if messagebox.askyesno('Save images', 'Slices loaded!\nSave slices as images?'):
        i = 0
        try:
            os.mkdir(patient_path + '/imgs/')
        except FileExistsError:
            pass
        for image in imgs:
            i += 1
            plt.imshow(image, cmap='gray', interpolation='bilinear')
            plt.savefig(patient_path + '/imgs/image_{}.jpg'.format(i), bbox_inches=None)

def process():
    if not glob(output_path + 'fullimages_*.npy'):
        messagebox.showinfo('Info', 'There are no patient files!')
        return
    files = [os.path.basename(i) for i in glob(output_path + 'fullimages_*.npy')]
    files = [re.sub(r'[fullimages_]', '', i) for i in files]
    files = [file.strip('.npy') for file in files]
    print(files)
    file_popup = tk.Toplevel()
    file_popup.title('Choose file')
    def file_choose(file):
        global chosen_file
        chosen_file = file
        print(file)
        file_popup.quit()
    for file in files:
        print(file)
        tk.Button(master=file_popup,
                  text='{}'.format(file),
                  command=lambda file=file: file_choose(file),
                  width=30,
                  height=3,
                  font='Arial, 11').pack()
    file_popup.mainloop()


    body_part = re.search(r'NECK', chosen_file) or re.search(r'CHEST', chosen_file) or re.search(r'PELVIS', chosen_file)
    body_part = body_part.group(0)
    print(body_part)
    imgs_to_process = np.load(output_path + 'fullimages_{}.npy'.format(chosen_file))
    slice = simpledialog.askinteger('Input', 'Choose slice:', parent=sample_stack(imgs_to_process))
    image3 = imgs_to_process[slice]

    plt.imshow(image3, cmap='gray', interpolation='bilinear')
    plt.show()
    if body_part == 'NECK':
        contourer = ContourerNeck()
    elif body_part == 'CHEST':
        contourer = ContourerChest()
    elif body_part == 'PELVIS':
        contourer = ContourerPelvis()
    else:
        raise BodyPartError('This localization is not supported!')


    contourer.contour(image3, save=False)

    answer = messagebox.askyesno('Save files', 'Save contoured images?')
    if answer:
        path = output_path + '/{}'.format(chosen_file)
        id = 0
        try:
            os.makedirs(path)
        except:
            pass
        for image in imgs_to_process:
            id += 1
            contourer.contour(image, path=path, save=True, id=id)


root = tk.Tk()

root.title('Menu')

tk.Button(text='Show Patient database', command=lambda: show_database(), font='Arial, 11', height=2).pack()
tk.Button(text='Reallocate and sort DICOM', command=lambda: sort(), font='Arial, 11', height=2).pack()
tk.Button(text='Load patient', command=lambda: patient_load(), font='Arial, 11', height=2).pack()
tk.Button(text='Process images', command=lambda: process(), font='Arial, 11', height=2).pack()
tk.Button(text='Quit', command=lambda: exit(), font='Arial, 11', height=2).pack()
root.mainloop()
