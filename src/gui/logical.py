import concurrent.futures
import math

from logic import *
import logic
import globals


# ========== functions for checking things/resetting
def keystroke_is_valid(pressed):
    return eval(pressed) == '1' or eval(pressed) == '2' or eval(pressed) == '9'


def robust_checking_needed(window, print_details=False):
    # no robust checking for train
    if window.data_mode == 'train':
        return False

    robust_levels = globals.params['robust_levels']
    min_length = globals.params['robust_min_length']

    current_length = window.high - window.low + 1
    length_match = True if current_length >= min_length else False  # doing ternary only for if length is is greater than some minimum
    level_match = True if window.comp_level <= robust_levels else False  # ternary only for the first robust_levels levels

    # return search_type_match and length_match and level_match
    if print_details:
        log(f'In [robust_checking_needed]: length_match: {length_match}, level_match: {level_match}')
    return length_match and level_match


def showing_window_for(window):  # could possibly add input_type which says if it is window or m1_rate, m2_rate directly
    if window.m1_rate is None and window.m2_rate is None:  # getting rate for m1
        return 'm1'

    elif window.m1_rate is not None and window.m2_rate is None:  # m1 already rated, getting rate for m2
        return 'm2'

    else:
        log(f'm1_rate: {window.m1_rate}, '
            f'm2_rate: {window.m2_rate}')
        raise NotImplementedError('Unexpected m1_rate '
                                  'm2_rate condition')


def calc_rule(m1_rate, m2_rate):
    if m1_rate == '1' and m2_rate == '1':
        return 'update_1'
    elif m1_rate == '2' and m2_rate == '2':
        return 'update_2'
    elif m1_rate == '1' and m2_rate == '2':
        return 'update_3'
    elif m1_rate == '9' and m2_rate == '2':
        return 'insert_m1'
    elif m1_rate == '1' and m2_rate == '9':
        return 'insert_m2'
    else:
        return 'inconsistency'


def matches_binary_insert_rule(window, rate):
    if window.data_mode == 'train':
        low_high_diff = window.high - window.low
        if rate == '9':
            log('In [matches_binary_insert_rule]: matches rule because 9 is pressed')
            return True
        if low_high_diff == 2 or low_high_diff == 1 or low_high_diff == 0:
            log(f'In [matches_binary_insert_rule]: matches rule because low_high_diff = {low_high_diff}')
            return True
    else:  # test rules
        if rate == '9' or window.high == window.low or (window.high - window.low == 1 and rate == '2'):
            return True
    return False


# ========== functions for changing window attributes
def init_or_use_rep(window, mid):
    rep = window.rep
    if rep is None:
        rep = bin_representative(which_bin=mid)
        window.rep = rep
        log(f'In [init_or_use_rep]: rep is None. '
            f'Calculated rep and set attribute to: {pure_name(window.rep)}')
    else:
        log(f'In [init_or_use_rep]: rep is already '
            f'set to: {pure_name(window.rep)}. Using the rep...')
    return rep


def init_or_use_anchor_and_rep(window):
    _curr_anchor = None
    _curr_rep = None  # only initialized and set in train mode

    # specifying the name of the anchor and representative to be used
    window_for = showing_window_for(window)  # 'm1' or 'm2'
    if window_for == 'm1':
        _curr_anchor_name = 'm1_anchor'
        _curr_rep_name = 'm1_rep'
    else:  # m2
        _curr_anchor_name = 'm2_anchor'
        _curr_rep_name = 'm2_rep'

    _curr_anchor = getattr(window, _curr_anchor_name)  # index in sorted list or index of the bin

    # init or use the anchor
    if _curr_anchor is None:
        _curr_anchor = calc_ternary_anchors(window)[window_for]
        setattr(window, _curr_anchor_name, _curr_anchor)
        log(f'In [init_or_use_anchor_and_rep]: {_curr_anchor_name} is None. '
            f'Calculated anchor and set attribute to: {_curr_anchor}')
    else:
        log(f'In [init_or_use_anchor_and_rep]: {_curr_anchor_name} already set to: {_curr_anchor}. '
            f'Using the anchor...')

    # init or use rep
    if window.data_mode == 'train':
        _curr_rep = getattr(window, _curr_rep_name)

        if _curr_rep is None:
            _curr_rep = bin_representative(which_bin=_curr_anchor)
            setattr(window, _curr_rep_name, _curr_rep)
            log(f'In [init_or_use_anchor_and_rep]: {_curr_rep_name} is None. '
                f'Calculated representative and set attribute to: {pure_name(_curr_rep)}')
        else:
            log(f'In [init_or_use_anchor_and_rep]: {_curr_rep_name} already set to: {pure_name(_curr_rep)}. '
                f'Using the representative...')

    return _curr_anchor, _curr_rep


def revert_attributes(window):
    # revert low, high indices
    window.current_index = window.prev_result['current_index']
    window.comp_level = window.prev_result['comp_level']
    window.low, window.high = window.prev_result['low'], window.prev_result['high']
    if window.data_mode == 'train':
        window.mid = window.prev_result['mid']
        log(f'In [revert_attributes]: reverted indices to: low = {window.low}, high = {window.high}, mid = {window.mid}')

    # for print purposes
    attrs_as_dict = {
        'current_index': window.current_index,
        'comp_level': window.comp_level,
        'low': window.low,
        'high': window.high,
    }

    # revert m1 and m2 rates
    if 'm1_rate' in window.prev_result.keys():
        window.m1_rate = window.prev_result['m1_rate']
        window.m2_rate = window.prev_result['m2_rate']

        attrs_as_dict['m1_rate'] = window.m1_rate
        attrs_as_dict['m2_rate'] = window.m2_rate

    # reset anchors
    if 'm1_anchor' in window.prev_result.keys():
        window.m1_anchor = window.prev_result['m1_anchor']
        window.m2_anchor = window.prev_result['m2_anchor']

        attrs_as_dict['m1_anchor'] = window.m1_anchor
        attrs_as_dict['m2_anchor'] = window.m2_anchor

    # revert bin representatives for train mode
    if 'm1_rep' in window.prev_result.keys():
        window.m1_rep = window.prev_result['m1_rep']
        window.m2_rep = window.prev_result['m2_rep']

        attrs_as_dict['m1_rep'] = window.m1_rep
        attrs_as_dict['m2_rep'] = window.m2_rep

    if 'rep' in window.prev_result.keys():
        window.rep = window.prev_result['rep']
        attrs_as_dict['rep'] = window.rep

    log(f'In [revert_attributes]: Reverted all attributes.')


def reset_attributes(window, exclude_inds=False, new_comp_level=None):
    if not exclude_inds:
        if window.data_mode == 'test':
            window.low = 0
            window.high = len(window.sorted_list) - 1

        else:
            window.low = 0
            window.high = len(window.bins_list) - 1
            log(f'In [reset_attributes]: calling calc_and_set_mid_for_train...')
            calc_and_set_mid_for_train(window)

    # reset comp level
    if new_comp_level is not None:
        window.comp_level = new_comp_level
    else:
        window.comp_level = 1

    if hasattr(window, 'm1_rate'):
        window.m1_rate = None

    if hasattr(window, 'm2_rate'):
        window.m2_rate = None

    if hasattr(window, 'm1_anchor'):
        window.m1_anchor = None

    if hasattr(window, 'm2_anchor'):
        window.m2_anchor = None

    if hasattr(window, 'm1_rep'):
        window.m1_rep = None

    if hasattr(window, 'm2_rep'):
        window.m2_rep = None

    if hasattr(window, 'rep'):
        window.rep = None

    log(f'In [reset_attributes]: attributes are reset for the new image.\n\n')


def reset_attributes_and_increase_index(window):
    reset_attributes(window)
    window.current_index += 1


def calc_ternary_anchors(window):
    low, high = window.low, window.high
    length = high - low

    m1 = low + int(length * (1/3))
    m2 = low + int(length * (2/3))

    anchors = {'m1': m1, 'm2': m2}
    return anchors


def update_ternary_indices(window, update_type):
    if update_type == 'update_1':
        window.low = window.m2_anchor

    elif update_type == 'update_2':
        window.high = window.m1_anchor

    elif update_type == 'update_3':
        window.low = window.m1_anchor
        window.high = window.m2_anchor

    else:
        raise NotImplementedError('In [update_ternary_indices]: unexpected update_type')


def is_in_lower_half(window):
    assert len(window.bins_list) == 8
    return window.high <= 3


def is_in_higher_half(window):
    assert len(window.bins_list) == 8
    return window.low >= 4


def calc_and_set_mid_for_train(window):
    float_mid = (window.low + window.high) / 2
    log(f'In [calc_and_set_mid_for_train]: low = {window.low}, high = {window.high}')

    # initial mid selection
    if window.low == 0 and window.high == len(window.bins_list) - 1:
        mid = random.choice([math.floor(float_mid), math.ceil(float_mid)])
        log(f'In [calc_mid_for_train]: float_mid = {float_mid}, RANDOMLY chosen mid: {mid}')
        # mid = 4
        # log(f'Hard-coded mid: {mid}')

    else:  # hard-coded for 8 bins
        if is_in_lower_half(window):
            mid = math.ceil(float_mid)
            log(f'In [calc_mid_for_train]: float_mid = {float_mid}, mid = {mid} CEILED since it is in the first lower half')

        elif is_in_higher_half(window):
            mid = math.floor(float_mid)
            log(f'In [calc_mid_for_train]: float_mid = {float_mid}, mid = {mid} FLOORED since it is in the first higher half')

        else:
            raise NotImplementedError
    window.mid = mid
    log(f'In [calc_mid_for_train]: window attributed mid set to: {mid}\n')
    return mid


def update_binary_inds(window, rate):
    mid = (window.low + window.high) // 2 if window.data_mode == 'test' else window.mid  # for train data, this represents bin number
    log(f'In [update_binary_inds]: mid is: {mid}')

    if window.data_mode == 'train':
        if rate == '1':
            window.low = mid + 1
            log(f'In [update_binary_inds]: low increased to {window.low}')
        else:  # '2'
            window.high = mid - 1
            log(f'In [update_binary_inds]: high decreased to {window.high}')

        # updating mid
        log(f'In [update_binary_inds]: calling calc_and_set_mid_for_train...')
        calc_and_set_mid_for_train(window)

    else:  # for data_mode test
        if rate == '1':  # rated as harder, go to the right half of the list
            window.low = mid if (window.high - window.low) > 1 else window.high
            log(f'In [binary_search_step]: '
                f'low increased to {window.low}')

        else:  # rated as easier, go to the left half of the list
            window.high = mid
            log(f'In [binary_search_step]: '
                f'high decreased to {window.high}')

    mid_str = f', mid = {window.mid}' if hasattr(window, "mid") else ""
    log(f'In [update_binary_inds]: Updated indices: low = {window.low}, high = {window.high}{mid_str}')


def insert_with_ternary_inds(window, anchor, item):
    if window.data_mode == 'test':
        insert_to_list(window.sorted_list, anchor, item)
        window.prev_result['insert_index'] = anchor
    else:
        pos = 'last' if globals.params['bin_rep_type'] == 'random' else 'before_last'
        insert_into_bin_and_save(which_bin=anchor, pos=pos, img=item)
        window.prev_result['insert_index'] = anchor
        window.prev_result['insert_pos'] = pos


def insert_with_binary_inds(window, rate, item):
    # for test data, we always round down to get the mid index, for train data, we do roudning in a symmteric way (see the paper)
    mid = (window.low + window.high) // 2 if window.data_mode == 'test' else window.mid  # for train data, mid represents bin number
    log(f'In [insert_with_binary_inds]: mid is: {mid}')

    if window.data_mode == 'test':
        if rate == '9' or rate == '2':  # 9 is pressed, so we insert directly
            insert_index = mid
        else:  # eval(pressed) == '1'
            insert_index = mid + 1

        insert_to_list(window.sorted_list, insert_index, item)
        window.prev_result.update({'insert_index': insert_index})
        log(f'In [insert_with_binary_inds]: inserted into index {insert_index} of sorted_list')

    # for train data
    else:
        # the first condition applies only to random representative, already checked in insertion rule
        if window.high - window.low == 2:
            which_bin = mid - 1 if rate == '2' else mid if rate == '9' else mid + 1
        elif window.high - window.low == 1:
            if is_in_lower_half(window):  # for lower_half bins, we have already rounded up to get mid bin
                which_bin = mid if (rate == '9' or rate == '1') else mid - 1
            elif is_in_higher_half(window):  # for higher_half we have already rounded down to get mid bin
                which_bin = mid if (rate == '9' or rate == '2') else mid + 1
            else:
                raise NotImplementedError
        else:  # 9 pressed or high = low
            which_bin = mid  # bin number to insert to
        bin_rep_type = globals.params['bin_rep_type']

        if bin_rep_type == 'random':  # for CSAW-M paper, we alway used 'random'
            pos = 'last'  # always last
        else:
            if rate == '9' or rate == '2':
                pos = 'before_last'  # image the new image is easier
            else:
                pos = 'last'  # if new image is harder

        log(f'In [insert_with_binary_inds]: bin_rep_type is "{bin_rep_type}", '
            f'inserting into position "{pos}" of bin {which_bin} - image: {pure_name(item)}')

        insert_into_bin_and_save(which_bin, pos, item)
        window.prev_result.update({'insert_index': which_bin, 'insert_pos': pos})


# ========== list-related functions
def remove_last_inserted(window):
    if window.data_mode == 'test':
        insertion_index = window.prev_result['insert_index']  # only in this case we have insertion index, otherwise it is None
        del window.sorted_list[insertion_index]  # delete the wrongly inserted element from the list
        log(f'In [remove_last_inserted]: index should be decreased ==> '
            f'removed index {insertion_index} from sorted_list - '
            f'Now sorted_list has len: {len(window.sorted_list)}')

        log(f'In [remove_last_inserted]: saving sorted_list with removed index...')
        write_sorted_list_to_file(window.sorted_list)

    else:  # e.g. prev_result: (left_img, right_img, rate, bin, 'last')
        which_bin, insert_pos = window.prev_result['insert_index'], window.prev_result['insert_pos']
        log(f'In [remove_last_inserted]: removing the "{insert_pos}" element from bin_{which_bin}.txt')
        del_from_bin_and_save(which_bin, insert_pos)


# ========== very generic functions
def window_attributes(window):
    as_dict = {
        'current_index': window.current_index,
        'low': window.low,
        'high': window.high
    }
    if hasattr(window, 'mid'):
        as_dict['mid'] = window.mid

    if hasattr(window, 'm1_anchor'):
        as_dict['m1_anchor'] = window.m1_anchor

    if hasattr(window, 'm2_anchor'):
        as_dict['m2_anchor'] = window.m2_anchor

    if hasattr(window, 'm1_rate'):
        as_dict['m1_rate'] = window.m1_rate

    if hasattr(window, 'm2_rate'):
        as_dict['m2_rate'] = window.m2_rate

    if hasattr(window, 'm1_rep'):
        as_dict['m1_rep'] = pure_name(window.m1_rep)

    if hasattr(window, 'm2_rep'):
        as_dict['m2_rep'] = pure_name(window.m2_rep)

    if hasattr(window, 'rep'):
        as_dict['rep'] = pure_name(window.rep)
    return as_dict


def shorten(dictionary):
    keys = ['m1_rep', 'm2_rep', 'rep']
    for key in keys:
        if key in dictionary.keys():
            dictionary[key] = pure_name(dictionary[key])
    return dictionary


def rate_to_text(rate):
    if rate == '1':
        return 'harder'
    elif rate == '2':
        return 'easier'
    else:
        return 'equal'


def load_left_right_images(window, threading=False):
    if threading:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            left_thread = executor.submit(logic.read_image_and_resize, window.curr_left_file)
            right_thread = executor.submit(logic.read_image_and_resize, window.curr_right_file)
            left_photo, right_photo = left_thread.result(), right_thread.result()
    else:
        left_photo = logic.read_image_and_resize(window.curr_left_file)
        right_photo = logic.read_image_and_resize(window.curr_right_file)
    return left_photo, right_photo


def log_current_index(window, called_from):
    log(f"\n\n\n\n{'=' * 150} \nIn [{called_from}]: "
        f"Current index: {window.current_index} - Case number: {window.case_number}\n", no_time=True)

    if window.session_name == 'sort':
        if window.data_mode != 'train':
            log(f'In [{called_from}]: There are {len(window.sorted_list)} images in the sorted_list\n', no_time=True)
        log(f'Showing window with attributes: \n{window_attributes(window)}\n', no_time=True)


def read_discarded_cases():
    discarded_file = globals.params['discarded']
    discarded_list = read_file_to_list(discarded_file)
    discarded_list = [parsed(discarded, '$')[0] for discarded in discarded_list]
    return discarded_list


def read_aborted_cases():
    aborted_file = globals.params['aborted']
    aborted_list = read_file_to_list(aborted_file)
    aborted_list = [parsed(aborted, '$')[0] for aborted in aborted_list]  # only the filename
    return aborted_list


def save_to_discarded_list(case, annotator, timestamp):
    filename = globals.params['discarded']
    string = f'{case} $ {annotator} $ {timestamp}'
    append_to_file(filename, string)
    log(f'In [save_to_discarded_list]: saved case "{case}" to discarded list.\n')


def save_to_aborted_list(case, annotator, timestamp):
    filename = globals.params['aborted']
    with open(filename, 'a') as file:
        string = f'{case} $ {annotator} $ {timestamp}'
        file.write(f'{string}\n')
    log(f'In [save_to_aborted_list]: saved case "{case}" to aborted list.')


def to_be_rated(data_mode):
    if data_mode == 'test':
        img_lst = helper.files_with_suffix(globals.params['test_imgs_dir'], '.png')
        already_sorted = read_sorted_imgs()
        n_bins = None
        text = 'sorted list len'
    else:
        img_lst = helper.files_with_suffix(globals.params['train_imgs_dir'], '.png')
        n_bins, already_sorted = all_imgs_in_all_bins()  # images that are already entered to bins
        text = 'total images in the bins'
    aborted_cases = read_aborted_cases()
    discarded_cases = read_discarded_cases()
    not_already_sorted = [img for img in img_lst if
                          (img not in already_sorted and img not in aborted_cases and img not in discarded_cases)]
    return img_lst, not_already_sorted, already_sorted, aborted_cases, discarded_cases, n_bins, text


def remove_last_record(from_file):
    if from_file == 'comparisons':
        file = globals.params['comparisons']
    elif from_file == 'aborted':
        file = globals.params['aborted']
    else:
        raise NotImplementedError

    records = read_file_to_list(file)
    records = records[:-1]
    write_list_to_file(records, file)
    log(f'In [remove_last_record]: removed the last record from "{from_file}" and saved it. \n')
