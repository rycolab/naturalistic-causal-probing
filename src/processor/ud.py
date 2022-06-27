import logging

import pandas as pd
from conllu import parse_incr
from conllu import parse_tree_incr

from constants import NORMAL, DIRECT_DEP, INDIRECT_DEP, FOCUS, IS_AMOD, \
    IS_DIRECT_CASE, \
    DIR_SUBJ
from src.reinflector.spa_base import SpaReinflector
from src.reinflector.utils import sentence_sanity_check
from src.util import util


class UdProcessor:
    def __init__(self, reinflector: SpaReinflector):
        self.sentences = []
        self.sentences_token_list = []
        self.reinflector = reinflector

    def reset_sentence_buffers(self):
        self.sentences_token_list = []
        self.sentences = []

    def process_file(self, ud_file, lang, output_file, **kwargs):
        # pylint: disable=unused-argument
        self.reinflector.df = []
        logging.info("Processing file %s", ud_file)
        data_file = open(ud_file, "r", encoding="utf-8")
        for token_tree in parse_tree_incr(data_file):
            self.sentences.append(token_tree)

        data_file = open(ud_file, "r", encoding="utf-8")
        for token_list in parse_incr(data_file):
            self.sentences_token_list.append(token_list)

        logging.info("PHASE TWO: parse trees")
        for sent_id, sent in enumerate(self.sentences):
            if not sentence_sanity_check(sent.metadata['text'],
                                         self.sentences_token_list[sent_id]):
                continue
            self.parse_tree(sent_id, sent, None, NORMAL, NORMAL, False, lang)

        logging.info("PHASE THREE: save csv file")
        util.write_csv(output_file, pd.DataFrame(self.reinflector.df))

    def setup_cache(self, cur_sent, node, target_focus_id):
        self.reinflector.cache.is_valid = True

        self.reinflector.cache.cur_sent = cur_sent
        self.reinflector.cache.cur_gender = node.token['feats']['Gender']
        self.reinflector.cache.cur_lemma = node.token['lemma']
        self.reinflector.cache.deprel = node.token['deprel']
        self.reinflector.cache.number = node.token['feats']['Number']

        self.reinflector.cache.cur_focus_idx = node.token['id'] - 1
        self.reinflector.cache.target_focus_idx = target_focus_id
        self.reinflector.cache.dep_tree_size = 1

        self.reinflector.cache.cur_adj_idx = -1
        self.reinflector.cache.cur_det_idx = -1

    def _mark_focus(self, sent_id, node, parent):
        temp_sent = [token.copy() for token in self.sentences_token_list[sent_id]]
        noun_is_ok, cur_sent_temp, target_focus_ids, offset = self.reinflector.reinflect_noun(
            temp_sent, node,
            parent)
        if noun_is_ok:
            self.setup_cache(cur_sent_temp, node, target_focus_ids)
            self.reinflector.cache.target_focus_idx += offset
        return noun_is_ok

    def _reinflect_indirect_deps(self, node, parent_state, new_parent_state):
        self.reinflector.cache.prev_node = None

        if parent_state == IS_AMOD and node.token['upos'] == 'ADJ':
            new_parent_state = IS_AMOD
            logging.debug("%s DOUBLE ADJ!!", node.token["form"])
            self.reinflector.reinflect_adj(self.reinflector.cache.cur_sent, node,
                                           self.reinflector.cache.prev_node)
        if parent_state == IS_DIRECT_CASE:
            if node.token['upos'] == 'DET':
                cur_sent = self.reinflector.cache.cur_sent
                prev_node = self.reinflector.cache.prev_node
                _, offset = self.reinflector.reinflect_det_pron("DET",
                                                                cur_sent,
                                                                node,
                                                                prev_node)
                self.reinflector.cache.target_focus_idx += offset
            elif node.token['form'].lower() == "del" or \
                    node.token['form'].lower() == "al":
                self.reinflector.cache.target_focus_idx += self.reinflector.reinflect_contraction(
                    self.reinflector.cache.cur_sent, node,
                    self.reinflector.cache.cur_gender)
        return new_parent_state

    def _reinflect_direct_deps(self, node, parent, state, new_parent_state):
        if node.token['deprel'] == 'det' or node.token['deprel'] == 'det:poss':
            cur_sent = self.reinflector.cache.cur_sent
            prev_node = self.reinflector.cache.prev_node
            _, offset = self.reinflector.reinflect_det_pron("DET",
                                                            cur_sent,
                                                            node,
                                                            prev_node)
            self.reinflector.cache.target_focus_idx += offset
            self.reinflector.cache.cur_det_idx = node.token['id'] - 1
        elif node.token['deprel'] == 'nsubj':
            noun_is_ok, _, _, offset = self.reinflector.reinflect_noun(
                self.reinflector.cache.cur_sent, node,
                parent)
            self.reinflector.cache.is_valid = self.reinflector.cache.is_valid and noun_is_ok
            self.reinflector.cache.target_focus_idx += offset
            state = DIR_SUBJ
        elif node.token['deprel'] == 'cop':
            is_valid, _ = self.reinflector.reinflect_verb(self.reinflector.cache.cur_sent,
                                                          node,
                                                          node, is_cop=True)
            self.reinflector.cache.is_valid = self.reinflector.cache.is_valid and is_valid
        elif node.token['deprel'] == 'acl' or node.token['deprel'] == 'appos':
            self.reinflector.cache.is_valid = False
        elif node.token['deprel'] == 'amod':
            new_parent_state = IS_AMOD
            self.reinflector.cache.cur_adj_idx = node.token['id'] - 1
            self.reinflector.reinflect_adj(self.reinflector.cache.cur_sent, node,
                                           self.reinflector.cache.prev_node)
        elif node.token['upos'] == 'PROPN':
            self.reinflector.cache.is_valid = False
        elif node.token['upos'] == 'PRON':
            cur_sent = self.reinflector.cache.cur_sent
            prev_node = self.reinflector.cache.prev_node
            is_valid, offset = self.reinflector.reinflect_det_pron("PRON",
                                                                   cur_sent,
                                                                   node,
                                                                   prev_node)
            if not is_valid:
                self.reinflector.cache.is_valid = False
            else:
                self.reinflector.cache.target_focus_idx += offset

        elif node.token['form'].lower() == "del" or node.token['form'].lower() == "al":
            self.reinflector.cache.target_focus_idx += self.reinflector.reinflect_contraction(
                self.reinflector.cache.cur_sent, node, self.reinflector.cache.cur_gender)
        elif node.token['deprel'] == 'case':
            new_parent_state = IS_DIRECT_CASE
        else:
            logging.debug("[NOT INFLECTED] %s: %s, %s", node.token['form'],
                          node.token['deprel'], node.token['upos'])
        return state, new_parent_state

    def _reinflect_parents(self, node, parent):
        if parent.token['upos'] == 'VERB':  # subject verb agreement
            is_valid, _ = self.reinflector.reinflect_verb(
                self.reinflector.cache.cur_sent, node,
                parent)
            self.reinflector.cache.is_valid = self.reinflector.cache.is_valid and is_valid
        else:  # it is subj of cop
            is_valid, _ = self.reinflector.reinflect_cop(
                self.reinflector.cache.cur_sent, node,
                parent)
            self.reinflector.cache.is_valid = self.reinflector.cache.is_valid and is_valid

            if parent.token['upos'] == 'DET' or parent.token['upos'] == 'PRON':
                is_valid, offset = self.reinflector.reinflect_det_pron(
                    parent.token['upos'],
                    self.reinflector.cache.cur_sent,
                    parent,
                    None)  ## TODO: prev node is not valid in this case
                self.reinflector.cache.is_valid = self.reinflector.cache.is_valid and is_valid
                self.reinflector.cache.target_focus_idx += offset
            elif parent.token['upos'] == 'ADJ':
                is_valid = self.reinflector.reinflect_adj(
                    self.reinflector.cache.cur_sent, parent,
                    None)
                self.reinflector.cache.is_valid = self.reinflector.cache.is_valid and is_valid

    def parse_tree(self, sent_id, node, parent, parent_state, state, ancestor_is_dependant,
                   lang):
        new_parent_state = NORMAL
        if node.token['deprel'] == 'acl' or node.token['deprel'] == 'appos':
            ancestor_is_dependant = True

        if state != DIRECT_DEP and state != INDIRECT_DEP and not ancestor_is_dependant and \
                node.token['upos'] == 'NOUN':
            if self._mark_focus(sent_id, node, parent):
                if node.token['deprel'] == 'nsubj' and parent is not None:
                    self._reinflect_parents(node, parent)
                state = FOCUS
            else:
                return

        if node.token['deprel'] == 'ccomp':
            self.reinflector.cache.is_valid = False
        if state != NORMAL:
            self.reinflector.cache.dep_tree_size += 1

        # Main logic of intervention
        if state == DIRECT_DEP:
            state, new_parent_state = self._reinflect_direct_deps(node, parent, state,
                                                                  new_parent_state)
            self.reinflector.cache.prev_node = node

        elif state == INDIRECT_DEP:
            new_parent_state = self._reinflect_indirect_deps(node, parent_state,
                                                             new_parent_state)

        for child in node.children:
            if state in (FOCUS, DIR_SUBJ):
                self.parse_tree(sent_id, child, node, new_parent_state, DIRECT_DEP,
                                ancestor_is_dependant, lang)
            elif state in (DIRECT_DEP, INDIRECT_DEP):
                self.parse_tree(sent_id, child, node, new_parent_state, INDIRECT_DEP,
                                ancestor_is_dependant, lang)
            else:
                self.parse_tree(sent_id, child, node, new_parent_state, NORMAL,
                                ancestor_is_dependant, lang)

        if state == FOCUS and self.reinflector.cache.is_valid:
            self.reinflector.add_sentence_to_df(sent_id, self.sentences_token_list[sent_id])
