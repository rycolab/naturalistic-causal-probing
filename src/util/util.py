import os
import pathlib
import pickle
import random
import shutil

import numpy as np
import torch


def config(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def write_csv(filename, results):
    results.to_csv(filename, index=False)


def write_data(filename, data):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def read_data(filename):
    with open(filename, "rb") as f:
        data = pickle.load(f)
    return data


def rmdir_if_exists(fdir):
    if os.path.exists(fdir):
        shutil.rmtree(fdir)


def file_len(fname):
    if not os.path.isfile(fname):
        return 0

    i = 0
    with open(fname, 'r') as f:
        for i, _ in enumerate(f):
            pass
    return i + 1


def mkdir(folder):
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
