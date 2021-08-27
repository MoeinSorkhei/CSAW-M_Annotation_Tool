from PIL import Image, ImageTk
import pydicom
import numpy as np

import globals
from .helper import log


def read_image_and_resize(file, save_to=None, extra_log=True, is_dicom=False):  # note the use of extra_log
    if is_dicom:  # backward compatibility, previously we used to read dicoms directly
        dataset = pydicom.dcmread(file)
        pixels = dataset.pixel_array
        pixels = pixels / np.max(pixels)  # normalize to 0-1, we do no futher preprocessing of dicom files

        orientation = str(dataset.get('PatientOrientation', "(missing)"))
        if 'A' in orientation:  # anterior view, should be flipped
            pixels = np.flip(pixels, axis=1)
        if extra_log:  # note: in case of using extra_log=True, 'output_path' should have already been set in globals.params
            log('', no_time=True)  # extra print in log file for more readability
        # update 27 Aug 2021: bone color space not needed
        # image = Image.fromarray(np.uint8(cm.bone(pixels) * 255))
        image = Image.fromarray(np.uint8(pixels * 255))  # rescale to 0-255 and convert to PIL Image
    else:  # now reading PNG images
        image = Image.open(file)

    # resize image
    resize_factor = globals.params['resize_factor']
    orig_width ,orig_height = image.size
    if resize_factor is not None:
        image = image.resize((orig_width // resize_factor, orig_height // resize_factor))

    if save_to:
        image.save(save_to)
    return image


# def image_list_to_png(image_list, save_path):
#     for filepath in image_list:  # image_list should have absolute file paths
#         png_filename = helper.pure_name(filepath).replace('.dcm', '.png')
#         final_name = os.path.join(save_path, png_filename)
#         read_image_and_resize(filepath, save_to=final_name, extra_log=False)
#         print('saved png to:', final_name)


# def convert_imgs_to_png(source_dir, dest_dir):
#     all_dicoms = sorted(glob.glob(f'{source_dir}/**/*.dcm', recursive=True))  # it assumes '/' path separator
#
#     for dicom_file in all_dicoms:
#         png_file = os.path.join(dest_dir, dicom_file.replace(f'{source_dir}/', '').replace('.dcm', '.png'))  # relative name
#         print(f'Doing for dicom: "{dicom_file}"')
#
#         sub_folders = os.path.split(png_file)[0]
#         helper.make_dir_if_not_exists(sub_folders, verbose=False)  # create all the sub-folders needed
#         read_image_and_resize(dicom_file, save_to=png_file)
#
#     print('In [convert_imgs_to_png]: all done')
