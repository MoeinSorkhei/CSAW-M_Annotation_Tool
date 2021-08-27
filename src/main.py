import argparse

import globals
from gui import *
from logic import *


def read_args_and_adjust():
    parser = argparse.ArgumentParser(description='Annotation tool')
    parser.add_argument('--annotator', type=str)
    parser.add_argument('--new', action='store_true')
    parser.add_argument('--already', action='store_true')
    parser.add_argument('--session_name', type=str, default='sort')
    parser.add_argument('--data_mode', type=str, default='train')
    parser.add_argument('--n_bins', type=int, default=12)
    parser.add_argument('--resize_factor', type=int)
    parser.add_argument('--max_imgs_per_session', type=int)
    parser.add_argument('--ui_verbosity', type=int)   # set be set to 2 for moderate verbosity

    parser.add_argument('--debug', action='store_true')

    arguments = parser.parse_args()

    if arguments.debug:
        globals.debug = True
        globals.params['resize_factor'] = 2

    if arguments.resize_factor:
        globals.params['resize_factor'] = arguments.resize_factor

    if arguments.max_imgs_per_session:
        globals.params['max_imgs_per_session'] = arguments.max_imgs_per_session
    return arguments


def show_window_with_keyboard_input(not_already_sorted, already_sorted, session_name,
                                    data_mode, annotator, ui_verbosity, train_bins=None):
    text = 'Which image is harder to be certain there is no tumor? (even the slightest difference is important)\n ' \
           'Press the corresponding button on the keyboard.'

    root = Tk()  # creates a blank window (or main window)
    title = Label(root, text=text, bg='light blue', font='-size 20')
    title.pack(fill=X)

    frame = Window(master=root,
                   cases=not_already_sorted,
                   already_sorted=already_sorted,
                   data_mode=data_mode,
                   session_name=session_name,
                   annotator=annotator,
                   ui_verbosity=ui_verbosity,
                   n_bins=train_bins)
    root.mainloop()  # run the main window continuously


def manage_sessions_and_run(args):
    session_name = args.session_name
    data_mode = args.data_mode
    annotator = args.annotator

    ui_verbosity = 1  # default, least verbose
    if globals.debug:
        ui_verbosity = 4
    elif args.ui_verbosity is not None:
        ui_verbosity = args.ui_verbosity

    # make seed list for annotator if this is the first time
    if args.session_name == 'sort' and args.data_mode == 'test' and args.new:
        write_list_to_file(globals.seed_list, globals.params['sorted'])
        log(f'Wrote seed list of len {len(globals.seed_list)} to: "{globals.params["sorted"]}"')

    # log indicating start of a session
    log(f"\n\n\n\n{'*' * 150} \n{'*' * 150} \n{'*' * 150} \n{'*' * 150}", no_time=True)
    log(f'Session started in {get_datetime()}')
    log(f'In [manage_sessions]: session_name: "{session_name}" - data_mode: {data_mode} - annotator: {annotator}')

    # adding current date and time to the ratings file, only for sort sessions
    if session_name == 'sort':
        with open(globals.params['ratings'], 'a') as rate_file:
            string = f'{"#" * 20} Ratings for session in {get_datetime()} - Data: {data_mode} - Annotator: {args.annotator}'
            rate_file.write(f'{string}\n')
            log('In [manage_sessions]: current session date time and the annotator written to the ratings file.\n')

    # not_already_sorted, already_sorted, n_bins = retrieve_not_already_sorted_files(session_name, data_mode)
    img_lst, not_already_sorted, already_sorted, aborted_cases, discarded_cases, n_bins, text = to_be_rated(data_mode)

    log(f'In [manage_sessions]: \n'
        f'read img_list of len: {len(img_lst)}\n'
        f'{text}: {len(already_sorted)} '
        f'({len([img for img in already_sorted if "train_imgs" in img])} train, {len([img for img in already_sorted if "test_imgs" in img])} test)\n'
        f'aborted cases: {len(aborted_cases)} \n'
        f'discarded cases: {len(discarded_cases)} \n'
        f'images left to be rated: {len(not_already_sorted)} \n')

    if len(not_already_sorted) == 0:
        log(f'In [main]: not_already_sorted images are of len: 0 ==> Session is already complete. Terminating...')
        exit(0)

    # reduce the number of images for a session to a ore-defined number
    max_imgs_per_session = globals.params['max_imgs_per_session']
    not_already_sorted = not_already_sorted[:max_imgs_per_session]
    log(f'In [manage_sessions]: not_already_sorted reduced to have len: {len(not_already_sorted)} in this session.')
    show_window_with_keyboard_input(not_already_sorted, already_sorted, session_name, data_mode, annotator, ui_verbosity, n_bins)


def set_global_paths(data_mode, annotator=None):
    # paths for the annotator (which are dependent on data_mode), ie, "../outputs_train/output_annotator" or "../outputs_test/output_annotator"
    annotator_path = get_annotator_path(data_mode, annotator)
    globals.params['output_path'] = annotator_path
    globals.params['ratings'] = os.path.join(annotator_path, 'ratings.txt')
    globals.params['discarded'] = os.path.join(annotator_path, 'discarded.txt')
    globals.params['error'] = os.path.join(annotator_path, 'error.txt')  # log.txt path is evaluate using output_path in log() function

    # text files for sorted and aborted are always in "../outputs_test/output_annotator"
    globals.params['sorted'] = os.path.join(get_annotator_path(data_mode='test', annotator=annotator), 'sorted.txt')
    globals.params['aborted'] = os.path.join(get_annotator_path(data_mode='test', annotator=annotator), 'aborted.txt')

def get_annotator_path(data_mode, annotator):
    return os.path.join(globals.params[f'output_path_{data_mode}'], f'output_{annotator}')  # outputs/output_Moein


def annotator_exists(data_mode, annotator):
    return os.path.exists(get_annotator_path(data_mode, annotator))


def check_args(args):
    if args.session_name != 'split' and args.annotator is None:
        message = 'Please provide annotator name using the --annotator argument'
        show_visual_error("Arguments specified incorrectly", message)
        exit(1)  # unsuccessful exit

    if args.session_name == 'sort':
        if not args.new and not args.already:  # one of the arguments should be specified
            message = 'Please use argument --new if it is the first time you are rating the images, or --already if you have already rated some images.'
            show_visual_error("Arguments specified incorrectly", message)
            exit(1)

        # checking for annotators paths
        annotator_out_path = get_annotator_path(args.data_mode, args.annotator)
        if args.new and os.path.exists(annotator_out_path):
            message = f'Another annotator with name {args.annotator} exists. If you have already used the tool, use \n --already.'
            show_visual_error("Arguments specified incorrectly", message)
            exit(1)

        if args.already and not os.path.exists(annotator_out_path):
            message = f'No annotator with name: {args.annotator} found. Are you specifying your name correctly?'
            show_visual_error("Arguments specified incorrectly", message)
            exit(1)


def main():
    args = read_args_and_adjust()
    check_args(args)  # make sure args are correct

    # check_args(args)
    if args.data_mode == 'train' or args.session_name == 'split':
        data_mode = 'train'
    elif args.data_mode == 'test':
        data_mode = 'test'
    else:
        raise NotImplementedError('In [main]: Config not recognized for determining data_mode')

    # setting all the needed global paths based on data_mode and annotator
    set_global_paths(data_mode=data_mode, annotator=args.annotator)

    # if session_name is split, sorted text file should necessarily exist
    if args.session_name == 'split' and not os.path.isfile(globals.params['sorted']):
        message = f'Sorted file corresponding to annotator "{args.annotator}" does not exist. Is the annotator already existent?'
        show_visual_error("Arguments specified incorrectly", message)
        exit(1)

    # from here onwards, the output folder and log file will be created if they do not exist
    print_global_paths(annotator=args.annotator)

    if args.session_name == 'split':
        split_sorted_list_to_bins(args.n_bins)
    else:  # session for sorting
        manage_sessions_and_run(args)


if __name__ == '__main__':
    main()
