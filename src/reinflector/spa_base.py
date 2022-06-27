import json
import logging
import os

import pandas as pd
from conllu import parse_incr
from tqdm import tqdm as tq

from constants import FEMININE, MASCULINE, ROOT_DIR
from src.reinflector.cache import CacheBase
from src.reinflector.utils import handle_case_match


class SpaReinflector:
    def __init__(self, ud_files):
        self.dets = {}
        self.prons = {}
        self.adjs = {}
        self.inanimate_lemmas = {}
        self.animate_lemmas = {}
        self.animate_dict = {}
        self.cops_dict = {}
        self.verbs_dict = {}

        self.profession_dict = {}
        self.lang = "spa"
        self.cache = CacheBase()
        self.df = []

        self.profession_path = os.path.join(ROOT_DIR, "data/manual/spa-profession.csv")

        self.initialize_dicts(ud_files)

    def initialize_animate_lemmata(self):
        profession_df = pd.read_csv(self.profession_path)
        for _, row in profession_df.iterrows():
            if row[MASCULINE] == "-" or row[FEMININE] == "-":
                continue
            self.profession_dict[row[MASCULINE]] = row[FEMININE]
            self.profession_dict[row[FEMININE]] = row[MASCULINE]

    def initialize_dicts(self, ud_files):
        logging.info("PHASE ONE: initializing dictionaries")
        for ud_file in ud_files:
            data_file = open(ud_file, "r", encoding="utf-8")
            for token_list in tq(parse_incr(data_file)):
                for item in token_list:
                    if item['feats']:
                        feats = item['feats']
                        if item['deprel'] == 'det' or item['deprel'] == 'det:poss':
                            feats["lemma"] = item['lemma']
                            self.dets[json.dumps(feats)] = item['form']
                        if item['upos'] == 'PRON':
                            feats["lemma"] = item['lemma']
                            self.prons[json.dumps(feats)] = item['form']

    def add_sentence_to_df(self, sent_id, sent_before):
        raise NotImplementedError()

    def reinflect_noun(self, cur_sent, node, parent):
        raise NotImplementedError()

    def reinflect_verb(self, cur_sent, node, verb_node, is_cop=False):
        raise NotImplementedError()

    def reinflect_cop(self, cur_sent, node, parent):
        raise NotImplementedError()

    def reinflect_contraction(self, cur_sent, node, cur_gender):
        raise NotImplementedError()

    def calc_reinflected_det_pron(self, node) -> str:
        raise NotImplementedError()

    def reinflect_det_pron(self, pos, cur_sent, node, prev_node):
        reinflected = None
        try:
            reinflected = self.calc_reinflected_det_pron(node)
        except NotImplementedError:
            print("Calc Reinflected String is Not Implemented")

        before = node.token['form']
        offset = 0

        if pos == "DET":
            target = self.dets
        else:
            target = self.prons
        if reinflected in target:
            after = target[reinflected]
            after = handle_case_match(before, after)

            if prev_node is not None:
                if (after == "el" and prev_node.token['form'] == "de") or (
                        after == "el" and prev_node.token['form'] == "a"):
                    if after == "el" and prev_node.token['form'] == "a":
                        after = "al"
                    else:
                        after = "del"
                    offset = -1
                    print("CONTRACTION")
                    prev_id = prev_node.token['id'] - 1
                    cur_sent[prev_id]['form'] = ""

            print("{} {} -> {}".format(pos, before, after))
            node_id = node.token['id'] - 1
            cur_sent[node_id]['form'] = after

            return True, offset
        print("MISSING DET/PRON REINFLECTION TOKEN")
        return False, offset

    def reinflect_adj(self, cur_sent, node, prev_node):
        raise NotImplementedError()

    @staticmethod
    def check_if_a_valid_noun(node):
        return node.token['feats'] is not None and 'Gender' in node.token[
            'feats'] and 'Number' in \
               node.token['feats']

    @staticmethod
    def reinflect_token(before, after, node_id, cur_sent):
        after = handle_case_match(before, after)
        cur_sent[node_id]['form'] = after
        return after
