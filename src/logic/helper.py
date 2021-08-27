import os
import json
from time import gmtime, strftime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import glob
import datetime
from shutil import copyfile
import random
import shutil

import globals


# ========== very generic functions
def read_params(params_path):
    with open(params_path, 'r') as f:  # reading params from the json file
        parameters = json.load(f)
    return parameters


def make_dir_if_not_exists(directory, verbose=True):  # note the use of verbose
    if not os.path.isdir(directory):
        os.makedirs(directory)
        if verbose:  # note: in case of using verbose=True, 'output_path' should have already been set in globals.params
            log(f'In [make_dir_if_not_exists]: created path "{directory}"')


def multi_log(to_be_logged):
    for string in to_be_logged:
        log(string)


def log(string, no_time=False):
    output_path = globals.params['output_path']
    make_dir_if_not_exists(output_path)
    print(string)
    # append string to the file with date and time
    line = f'{string}\n' if no_time else f'[{get_datetime(raw=True)}] $ {string}\n'
    log_file = os.path.join(output_path, 'log.txt')
    with open(log_file, 'a') as file:
        file.write(line)


def print_and_wait(string):
    print(string)
    print('====== Waiting for input')
    input()


def split_to_lines(inp):
    if len(inp) == 3:
        string = f'({inp[0]}, \n{inp[1]}, {inp[2]})'
    else:
        string = f'({inp[0]}, {inp[1]})'
    return string


def pure_name(file_path):
    if file_path is None:
        return None
    return file_path.split(os.path.sep)[-1]


def pure_names(the_list, sep):
    assert type(the_list) == list, 'Input should be of type list'
    return [filename.split(sep)[-1] for filename in the_list]


def replace_all(lst, old_str, new_str):
    return [file.replace(old_str, new_str) for file in lst]


def prepend_to_paths(the_list, string):
    assert string.endswith('/'), 'String should end with /'
    return [f'{string}{filename}' for filename in the_list]


def files_with_suffix(directory, suffix):
    files = [os.path.abspath(path) for path in glob.glob(f'{directory}/**/*{suffix}', recursive=True)]  # full paths
    return files


def print_list(sorted_list):
    log('________________________________________________________________', no_time=True)
    log(f'In [binary_search_step]: sorted_list:')
    for item in sorted_list:
        log(item, no_time=True)
    log('________________________________________________________________\n\n', no_time=True)


def read_file_to_list(filename):
    lines = []
    if os.path.isfile(filename):
        with open(filename) as f:
            lines = f.read().splitlines()
    return lines


def write_list_to_file(lst, filename):
    with open(filename, 'w') as f:
        for item in lst:
            f.write(f'{item}\n')


def append_to_file(filename, item):
    with open(filename, 'a') as file:
        file.write(f'{item}\n')


def insert_to_list(lst, pos, item):
    lst.insert(pos, item)
    write_sorted_list_to_file(lst)
    log(f'In [insert_to_list]: Now sorted list has len: {len(lst)}')


def shorten_file_name(filename):
    if len(filename) < 10:
        return filename
    else:
        return '...' + filename[-15:]


def get_all_dicom_files(img_folder):
    return glob.glob(f'{img_folder}/**/*.dcm', recursive=True)  # it assumes '/' path separator


def get_datetime(raw=False, underscored=False):
    if underscored:
        return datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    elif raw:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")


def print_global_paths(annotator=None):
    orig_rating_str = f'\norig_ratings: {globals.params["orig_ratings"]}' if 'orig_ratings' in globals.params.keys() else ''
    log(f"\n\n\n\n{'#' * 150}", no_time=True)
    log(
        f'In [main]: Checking paths for annotator: {annotator} and output_path: "{globals.params["output_path"]}" done.\n'
        f"output_path: {globals.params['output_path']}\n"
        f"ratings: {globals.params['ratings']}"
        f"discarded: {globals.params['discarded']}\n"
        f"error: {globals.params['error']}\n"
        f"sorted: {globals.params['sorted']}\n"
        f"aborted: {globals.params['aborted']}\n"
        f"{orig_rating_str}")
    log(f"{'#' * 150}", no_time=True)


def subtract_lists(list1, list2):
    return [x1 - x2 for (x1, x2) in zip(list1, list2)]


# ========== functions for saving/reading results
def write_sorted_list_to_file(lst):
    sorted_filename = globals.params['sorted']

    with open(sorted_filename, 'w') as f:
        for item in lst:
            f.write(f'{item}\n')
    log(f'In [write_sorted_list_to_file]: wrote sorted list to {sorted_filename}: done \n')

    if globals.debug:
        print_list(lst)


def save_rating(left_img, right_img, rate, annotator, timestamp):
    rate_file = globals.params['ratings']
    with open(rate_file, 'a') as f:
        string = f'{left_img} $ {right_img} $ {rate} $ {annotator} $ {timestamp}'
        f.write(f'{string}\n')


def remove_last_rating():
    rate_file = globals.params['ratings']
    remove_last_line_from_file(rate_file)


def remove_last_aborted():
    aborted_file = globals.params['aborted']
    remove_last_line_from_file(aborted_file)


def remove_last_line_from_file(filename):
    lines = read_file_to_list(filename)
    lines = lines[:-1]
    write_list_to_file(lines, filename)


def _parse_ratings():
    ratings_file = globals.params['ratings']
    ratings = read_file_to_list(ratings_file)

    parsed_ratings = []
    for rating in ratings:
        if rating.startswith('#'):  # this is separator between sessions
            continue
        left_file, right_file, rate, annotator, timestamp = rating.split('$')
        parsed_ratings.append((left_file.strip(), right_file.strip(), rate.strip(), annotator.strip(), timestamp.strip()))
    return parsed_ratings


def left_right_substr(string):
    # given a string like "2.dcm $ 33.dcm $ 9 $ Moein $ 2020-09-22_09:23:22", it returns "2.dcm $ 33.dcm"
    left, right = parsed(string, '$')[:2]
    return f'{left} $ {right}'


def parsed(string, character):
    return [item.strip() for item in string.split(character)]


def get_rate_if_already_exists(left_file, right_file):
    parsed_ratings = _parse_ratings()
    for record in parsed_ratings:
        if record[0] == left_file and record[1] == right_file:
            return record[2]  # the rate
    return None
