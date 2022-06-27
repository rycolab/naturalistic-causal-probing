import argparse
import os
import sys

import torch

print(os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from src.processor import UdProcessor
from src.util import util
from src.util.ud_list import UD_LIST
from src.reinflector.spa_gender import SpaGenderReinflector
from src.reinflector.spa_number import SpaNumberReinflector
from constants import ROOT_DIR


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--batch-size",
                        help="The size of the mini batches",
                        default=8,
                        required=False,
                        type=int)
    parser.add_argument("--language",
                        help="The language to use",
                        default='spa',
                        type=str)
    parser.add_argument("--ud-file-name",
                        help="The name of UD dataset, for spanish choose between spa-ancora"
                             " and spa-gsd",
                        required=True,
                        default='',
                        type=str)
    parser.add_argument("--reinflector",
                        help="Choose between gender and number",
                        required=True,
                        default='gender',
                        type=str)
    parser.add_argument("--ud-path",
                        help="The path to raw ud data",
                        default='data/ud/ud-treebanks-v2.6/',
                        required=False,
                        type=str)
    parser.add_argument("--output-path",
                        help="The path to save processed data",
                        default='../data/processed/',
                        required=False,
                        type=str)
    args = parser.parse_args()
    print(args)

    return args


def get_ud_file_base(ud_path, ud_filename):
    return os.path.join(ud_path, UD_LIST[ud_filename])


def get_data_file_base(output_path, language):
    output_path = os.path.join(output_path, language)
    util.mkdir(output_path)
    return os.path.join(output_path, '%s.csv')


def get_data_processor(ud_path, args):
    ud_file_base = get_ud_file_base(ud_path, args.ud_file_name)
    ud_files = [ud_file_base % mode for mode in ['train', 'dev', 'test']]

    if args.language == 'spa':
        if args.reinflector == 'gender':
            inflector = SpaGenderReinflector(ud_files)
        elif args.reinflector == 'number':
            inflector = SpaNumberReinflector(ud_files)
        else:
            inflector = None
        processor = UdProcessor(inflector)
    else:
        raise ValueError('Invalid Processor')

    return processor


def process(language, ud_path, args):
    print("Loading data processor")
    processor = get_data_processor(ud_path, args)

    print("Precessing language %s" % language)
    ud_file_base = get_ud_file_base(ud_path, args.ud_file_name)
    output_file_base = get_data_file_base(args.output_path, language)

    for mode in ['train', 'dev', 'test']:
        processor.reset_sentence_buffers()
        ud_file = ud_file_base % mode
        output_file = output_file_base % mode
        processor.process_file(ud_file, language, output_file, batch_size=args.batch_size)

    print("Process finished")


def main():
    args = get_args()

    language = args.language
    ud_path = args.ud_path
    ud_path = os.path.join(ROOT_DIR, ud_path)

    with torch.no_grad():
        process(language, ud_path, args)


if __name__ == "__main__":
    main()
