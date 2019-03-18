import os
import sys
import re
import json
import getpass
import threading
from glob import glob

import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from tkinter.filedialog import askdirectory
from terminaltables import AsciiTable
from pony.orm import commit
from pony.orm.core import ObjectNotFound

import db_template
from sorter import SorterByID, SorterByName
from handler import ScanReader, sample_stack, ContourerNeck, ContourerChest, ContourerPelvis, Plot3D
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

    def delete():

        id = simpledialog.askstring('Choose patient', 'Choose patient ID to delete:')
        try:
            db_template.PatientData[id].delete()
            commit()
            root.quit()
            root.destroy()
            show_database()
        except ValueError:
            pass
        except ObjectNotFound:
            messagebox.showinfo('Info', 'No such patient')

    try:
        db_template.db.bind(provider='sqlite', filename='patients.sqlite', create_db=False)
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

    data = [('ID', 'Name', 'Sex', 'Birth Date', 'Body part', 'Study Date')] + data
    table = AsciiTable(data, title='Patient database')
    root = tk.Toplevel()
    root.configure(bg='white')
    root.title('Patient Database')
    tk.Label(root, text=table.table, background='white', font='Arial, 11').pack()
    tk.Button(root, text='OK', command=lambda: close(), bg='white').pack()
    tk.Button(root, text='Delete ', command=lambda: delete(), bg='white').pack()
    root.mainloop()


def sort():

    try:
        tk.Tk().withdraw()
        data_path = askdirectory()
        global working_path, g

        g = glob(data_path + '/*.dcm')
    except TypeError:
        return

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

    try:
        patient_path = askdirectory()
        patient = Patient(patient_path)
    except (IndexError, TypeError):
        return
    patient_params = {'Patient ID': patient.get_id(),
                      'Patient Name': patient.get_name(),
                      'Patient Sex': patient.get_sex(),
                      'Birth Date': patient.get_birth_date(),
                      'Body part examined': patient.get_body_part(),
                      'Study Date': patient.get_study_date()
                      }

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
            commit()
        except:
            pass

        @db_template.db_session
        def enter_patient(id, name, sex, birthday, body_part, study_date):

            db_template.PatientData(id=id, name=name, sex=sex, birthday=birthday, body_part=body_part, study_date=study_date)
            commit()

        try:
            enter_patient(patient_params['Patient ID'],
                          patient_params['Patient Name'],
                          patient_params['Patient Sex'],
                          patient_params['Birth Date'],
                          patient_params['Body part examined'],
                          patient_params['Study Date']
                          )
        except:
            messagebox.showinfo('Info', 'Patient already in the database!')
            return

    patient_scans = reader.load_scan(patient_path)
    imgs = reader.get_pixels_hu(patient_scans)

    id = patient_params['Patient ID']
    name = patient_params['Patient Name']
    body_part = patient_params['Body part examined']
    np.save(output_path + "fullimages_{}({}, {}).npy".format(id, name, body_part), imgs)

    imgs = np.load(output_path + 'fullimages_{}({}, {}).npy'.format(id, name, body_part))

    if messagebox.askyesno('Save images', 'Slices loaded!\nSave slices as images?'):
        def set_extension(frmt):
            global ext
            ext=frmt
            fmt.quit()
            fmt.destroy()

        fmt = tk.Toplevel()
        fmt.title('Choose format')
        tk.Button(master=fmt, text='jpg', command=lambda: set_extension('jpg'), font='Arial, 11').pack()
        tk.Button(master=fmt, text='png', command=lambda: set_extension('png'), font='Arial, 11').pack()
        tk.Button(master=fmt, text='tiff', command=lambda: set_extension('tiff'), font='Arial, 11').pack()
        fmt.mainloop()

        i = 0
        try:
            os.mkdir(patient_path + '/imgs/')
        except FileExistsError:
            pass
        for image in imgs:
            i += 1
            plt.imshow(image, cmap='gray', interpolation='bilinear')
            plt.savefig(patient_path + '/imgs/image_{}.{}'.format(i, ext), bbox_inches=None)
            plt.clf()


def process():
    if not glob(output_path + 'fullimages_*.npy'):
        messagebox.showinfo('Info', 'There are no patient files!')
        return
    files = [os.path.basename(i) for i in glob(output_path + 'fullimages_*.npy')]
    files = [re.sub(r'[fullimages_]', '', i) for i in files]
    files = [file.strip('.npy') for file in files]
    file_popup = tk.Toplevel()
    file_popup.title('Choose file')

    def file_choose(file):
        global chosen_file
        chosen_file = file
        file_popup.quit()
        file_popup.destroy()
    for file in files:
        tk.Button(master=file_popup,
                  text='{}'.format(file),
                  command=lambda file=file: file_choose(file),
                  width=30,
                  height=2,
                  font='Arial, 10').pack()
    file_popup.mainloop()

    body_part = re.search(r'NECK', chosen_file) or re.search(r'CHEST', chosen_file) or re.search(r'PELVIS', chosen_file)
    body_part = body_part.group(0)
    imgs_to_process = np.load(output_path + 'fullimages_{}.npy'.format(chosen_file))

    plt.hist(imgs_to_process.flatten(), bins=15, color='green')
    plt.xlabel("Hounsfield Units (HU)")
    plt.ylabel("Frequency")
    plt.show()

    while True:
        try:
            slice = simpledialog.askinteger('Input', 'Choose slice:', parent=sample_stack(imgs_to_process))
            image = imgs_to_process[slice]
        except IndexError:
            messagebox.showinfo('Info', 'Wrong number!')
            continue
        break

    plt.imshow(image, cmap='gray', interpolation='bilinear')
    plt.show()
    if body_part == 'NECK':
        contourer = ContourerNeck()
    elif body_part == 'CHEST':
        contourer = ContourerChest()
    elif body_part == 'PELVIS':
        contourer = ContourerPelvis()
    else:
        raise BodyPartError('This localization is not supported!')

    contourer.contour(image, save=False)

    answer = messagebox.askyesno('Save files', 'Save contoured images?')
    if answer:

        def set_extension(frmt):
            global ext
            ext=frmt
            fmt.quit()
            fmt.destroy()

        fmt = tk.Toplevel()
        fmt.title('Choose format')
        tk.Button(master=fmt, text='jpg', command=lambda: set_extension('jpg'), font='Arial, 11').pack()
        tk.Button(master=fmt, text='png', command=lambda: set_extension('png'), font='Arial, 11').pack()
        tk.Button(master=fmt, text='tiff', command=lambda: set_extension('tiff'), font='Arial, 11').pack()
        fmt.mainloop()

        path = output_path + '/{}'.format(chosen_file)

        try:
            os.makedirs(path)
        except:
            pass
        root = tk.Toplevel()
        root.title('Progress')
        pb = ttk.Progressbar(root, mode='determinate')
        pb.pack()
        def progress():
            id = 0
            for image in imgs_to_process:
                id += 1
                pb['value'] += 1
                contourer.contour(image, path=path, save=True, id=id, format=ext)
            root.destroy()
        threading.Thread(target=progress).start()
        root.mainloop()


def make_3d():
    if not glob(output_path + 'fullimages_*.npy'):
        messagebox.showinfo('Info', 'There are no patient files!')
        return
    files = [os.path.basename(i) for i in glob(output_path + 'fullimages_*.npy')]
    files = [re.sub(r'[fullimages_]', '', i) for i in files]
    files = [file.strip('.npy') for file in files]

    file_popup = tk.Toplevel()
    file_popup.title('Choose file')

    def file_choose(file):
        global chosen_file
        chosen_file = file
        file_popup.quit()
        file_popup.destroy()
    for file in files:
        tk.Button(master=file_popup,
                  text='{}'.format(file),
                  command=lambda file=file: file_choose(file),
                  width=30,
                  height=2,
                  font='Arial, 10').pack()
    file_popup.mainloop()

    # Have to choose dir with DICOM files of chosen patient
    patient_path = askdirectory()

    plot3d_maker = Plot3D()
    reader = ScanReader()

    imgs_to_process = np.load(output_path + 'fullimages_{}.npy'.format(chosen_file))
    patient = reader.load_scan(patient_path)

    imgs_after_resamp, spacing = plot3d_maker.resample(imgs_to_process, patient, [1, 1, 1])

    v, f = plot3d_maker.make_mesh(imgs_after_resamp, 350, 2)
    plot3d_maker.plotly_3d(v, f, output_path, chosen_file)

def show_images():
    if not glob(output_path + 'fullimages_*.npy'):
        messagebox.showinfo('Info', 'There are no patient files!')
        return
    files = [os.path.basename(i) for i in glob(output_path + 'fullimages_*.npy')]
    files = [re.sub(r'[fullimages_]', '', i) for i in files]
    files = [file.strip('.npy') for file in files]

    file_popup = tk.Toplevel()
    file_popup.title('Choose file')

    def file_choose(file):
        global chosen_file
        chosen_file = file
        file_popup.quit()
        file_popup.destroy()
    for file in files:
        tk.Button(master=file_popup,
                  text='{}'.format(file),
                  command=lambda file=file: file_choose(file),
                  width=30,
                  height=2,
                  font='Arial, 10').pack()
    file_popup.mainloop()

    images = np.load(output_path + 'fullimages_{}.npy'.format(chosen_file))

    while True:
        try:
            slice = simpledialog.askinteger('Input', 'Choose slice:', parent=sample_stack(images))
            image = images[slice]
        except IndexError:
            messagebox.showinfo('Info', 'Wrong number!')
            continue
        break

    plt.imshow(image, cmap='gray', interpolation='bilinear')
    plt.show()

root = tk.Tk()
root.title('Menu')

tk.Button(text='Show Patient database', command=lambda: show_database(), font='Arial, 11', height=2).pack()
tk.Button(text='Reallocate and sort DICOM', command=lambda: sort(), font='Arial, 11', height=2).pack()
tk.Button(text='Load patient', command=lambda: patient_load(), font='Arial, 11', height=2).pack()
tk.Button(text='Show images', command=lambda: show_images(), font='Arial, 11', height=2).pack()
tk.Button(text='Process images', command=lambda: process(), font='Arial, 11', height=2).pack()
tk.Button(text='Make 3D image', command=lambda: make_3d(), font='Arial, 11', height=2).pack()
tk.Button(text='Quit', command=lambda: sys.exit(), font='Arial, 11', height=2).pack()
root.mainloop()
