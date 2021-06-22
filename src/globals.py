import os

# ===== running the program in debug mode
debug = False

params = {
    "test_basenames": os.path.join('..', 'data', 'test_basenames.txt'),
    "train_basenames": os.path.join('..', 'data', 'train_basenames.txt'),

    "test_imgs_dir": os.path.join('..', 'data', 'test_imgs'),  # for test data
    "train_imgs_dir": os.path.join('..', 'data', 'train_imgs'),  # for train data

    "data_path": os.path.join('..', 'data'),

    "output_path_test": os.path.join('..', 'outputs_test'),
    "output_path_train": os.path.join('..', 'outputs_train'),

    "show_border_time": 100,  # in milliseconds
    "robust_levels": 2,  # ternary search is done only for the first 2 levels, after which binary search will be done
    "robust_min_length": 4,  # minimum length of sorted list valid for doing ternary, ternary does not makes sense for length smaller than this
    "bin_rep_type": 'random',  # or 'last': specifies how the bin representative should be chosen

    "max_imgs_per_session": 10000,
    "resize_factor": 4
}
