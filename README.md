# dicom-handler

A simple handler which allows performing several manipulations with DICOM files with CT modality. 
It scans, for example, a directory with incoming files from CT and reallocates them by folders named as full names or IDs of patients (and date of the study).
Next, such operations may be performed:
  - add a patient to the SQLite database
  - show a stack of slices and then a specific slice
  - save slices of scans as images
  - apply simple contours to the structures (for neck, chest and pelvis localizations)
  - create a 3D reconstruction of the scans (Requires IPython)

![alt text](https://github.com/aleksei-zrk/dicom-handler/blob/master/screenshots/screenshot_2.jpeg)

![alt text](https://github.com/aleksei-zrk/dicom-handler/blob/master/screenshots/screenshot_3.jpeg)

![alt text](https://github.com/aleksei-zrk/dicom-handler/blob/master/screenshots/screenshot_4.jpg)
