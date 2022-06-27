import json

from conllu import parse_incr
from tqdm import tqdm as tq

from constants import PLURAL, FEMININE, MASCULINE
from .cache import CacheBase
from .spa_base import SpaReinflector
from .utils import swap_gender, handle_case_match, check_if_inanimated, \
    parse_reinflected_sentence


def _reinflect_plural_adj(new_gender, adj_lemma, before):
    if adj_lemma[-1] == "o" and new_gender == FEMININE:
        after = before[:-2] + "as"
    elif adj_lemma[-1] == "o" and new_gender == MASCULINE:
        after = before[:-2] + "os"
    elif adj_lemma[-2:] == "ón" and new_gender == FEMININE:
        after = before[:-2] + "as"
    elif adj_lemma[-2:] == "ón" and new_gender == MASCULINE:
        after = before[:-2] + "es"
    elif adj_lemma[-2:] == "ín" and new_gender == FEMININE:
        after = before[:-2] + "as"
    elif adj_lemma[-2:] == "ín" and new_gender == MASCULINE:
        after = before[:-2] + "es"
    elif (adj_lemma[-2:] == "or" and adj_lemma[-5:] != "erior") and new_gender == FEMININE:
        after = before[:-2] + "as"
    elif (adj_lemma[-2:] == "or" and adj_lemma[-5:] != "erior") and new_gender == MASCULINE:
        after = before[:-2] + "es"
    else:
        after = before
    return after


def _reinflect_singular_adj(new_gender, adj_lemma, before):
    if adj_lemma[-1] == "o" and new_gender == FEMININE:
        after = before[:-1] + "a"
    elif adj_lemma[-1] == "o" and new_gender == MASCULINE:
        after = adj_lemma
    elif adj_lemma[-2:] == "ón" and new_gender == FEMININE:
        after = before[:-2] + "ona"
    elif adj_lemma[-2:] == "ón" and new_gender == MASCULINE:
        after = adj_lemma
    elif adj_lemma[-2:] == "ín" and new_gender == FEMININE:
        after = before[:-2] + "ina"
    elif adj_lemma[-2:] == "ín" and new_gender == MASCULINE:
        after = adj_lemma
    elif adj_lemma[-2:] == "or" and adj_lemma[-5:] != "erior" and new_gender == FEMININE:
        after = before + "a"
    else:
        after = before
    return after


class SpaGenderReinflector(SpaReinflector):
    def __init__(self, ud_files):
        super().__init__(ud_files)
        self.initialize_animate_lemmata()
        self.cache = CacheBase()

    def add_item_to_gender_lemma_dict(self, number, gender, form, is_animated):
        if is_animated:
            target = self.animate_lemmas
        else:
            target = self.inanimate_lemmas
        if number not in target:
            target[number] = [(form, gender)]
        elif (form, gender) not in target[number] and is_animated:
            target[number].append((form, gender))
            new_gender = swap_gender(gender)
            target[number].append((self.profession_dict[form], new_gender))
        elif not is_animated:
            target[number].append((form, gender))

    def initialize_dicts(self, ud_files):
        super().initialize_dicts(ud_files)
        for ud_file in ud_files:
            data_file = open(ud_file, "r", encoding="utf-8")

            for gender_token_list in tq(parse_incr(data_file)):
                for item in gender_token_list:
                    if not item['feats']:
                        continue
                    feats = item['feats']
                    if item['upos'] == 'NOUN' and \
                            'Gender' in item['feats'] and \
                            'Number' in item['feats']:
                        if check_if_inanimated(item, self.lang):
                            self.add_item_to_gender_lemma_dict(feats['Number'],
                                                               feats['Gender'],
                                                               item['form'], False)

                        if item['form'] in self.profession_dict:
                            self.add_item_to_gender_lemma_dict(feats['Number'],
                                                               feats['Gender'],
                                                               item['form'], True)

    def add_sentence_to_df(self, sent_id, sent_before):
        cur_gender = self.cache.cur_gender
        res_dict = {'ID': sent_id, 'focus': self.cache.cur_lemma,
                    'focus ID': self.cache.cur_focus_idx,
                    'adj idx': self.cache.cur_adj_idx,
                    'det idx': self.cache.cur_det_idx,
                    "before": parse_reinflected_sentence(sent_before),
                    "before gender": self.cache.cur_gender, "deprel": self.cache.deprel,
                    'number': self.cache.number, "dep tree size": self.cache.dep_tree_size}

        print(sent_id, ": " + parse_reinflected_sentence(self.cache.cur_sent))

        all_tokens = parse_reinflected_sentence(self.cache.cur_sent).split()
        after_sent, offset = self.postprocess_contractions(all_tokens)
        res_dict["after"] = after_sent
        res_dict["focus ID after"] = self.cache.target_focus_idx + offset
        res_dict["after gender"] = swap_gender(cur_gender)

        self.df.append(res_dict)

        self.cache.reset_values()

    def reinflect_noun(self, cur_sent, node, parent):
        if not SpaReinflector.check_if_a_valid_noun(node):
            return False, cur_sent, node.token['id'] - 1, 0
        before = node.token['form']
        if before.lower() not in self.profession_dict:
            return False, cur_sent, node.token['id'] - 1, 0

        before = node.token['form']
        after = self.profession_dict[before.lower()]

        after = handle_case_match(before, after)
        print("NOUN {} -> {}".format(before, after))

        node_id = node.token['id'] - 1
        cur_sent[node_id]['form'] = after

        return True, cur_sent, node.token['id'] - 1, 0

    def calc_reinflected_det_pron(self, node):
        reinflected = node.token['feats'].copy()
        reinflected["lemma"] = node.token['lemma']
        reinflected["Gender"] = swap_gender(reinflected["Gender"])
        reinflected = json.dumps(reinflected)

        return reinflected

    def reinflect_det_pron(self, pos, cur_sent, node, prev_node):
        if 'feats' not in node.token or node.token['feats'] is None or "Gender" not in \
                node.token['feats']:
            return False, 0
        return super().reinflect_det_pron(pos, cur_sent, node, prev_node)

    def reinflect_contraction(self, cur_sent, node, cur_gender):
        new_gender = swap_gender(cur_gender)
        before = node.token['form']
        after = before
        offset = 0
        if new_gender == FEMININE:
            if before.lower() == "del":
                after = "de la"
                offset += 1
                print("CONTRACTION {} -> {}".format(before, after))
            elif before.lower() == "al":
                after = "a la"
                offset += 1
        else:
            after = before
        node_id = node.token['id'] - 1
        self.reinflect_token(before, after, node_id, cur_sent)
        return offset

    def reinflect_adj(self, cur_sent, node, prev_node):
        if node.token['feats'] is None or "Gender" not in \
                node.token['feats'] or "Number" not in \
                node.token['feats']:
            return False
        new_gender = swap_gender(node.token['feats']["Gender"])
        adj_lemma = node.token['lemma']
        before = node.token['form']

        if adj_lemma[-3:] == "ista" or adj_lemma[-3:] == "e":
            after = before

        elif node.token['feats']['Number'] != PLURAL:
            after = _reinflect_singular_adj(new_gender, adj_lemma, before)

        else:
            after = _reinflect_plural_adj(new_gender, adj_lemma, before)

        node_id = node.token['id'] - 1
        after = self.reinflect_token(before, after, node_id, cur_sent)
        print("ADJ {} -> {}".format(before, after))
        return True

    def reinflect_verb(self, cur_sent, node, verb_node, is_cop=False):
        return True, cur_sent

    def reinflect_cop(self, cur_sent, node, parent):
        return True, cur_sent

    @staticmethod
    def postprocess_contractions(all_tokens):
        "this function handles the contractions and adjusts tokens' indices accordingly"
        all_tokens.append("")
        prev_token = ""
        after_sent = ""

        idx = 0
        offset = 0

        while idx < len(all_tokens):
            if prev_token == "a" and all_tokens[idx] == "el":
                after_sent += "al"
                offset -= 1
            elif prev_token == "de" and all_tokens[idx] == "el":
                after_sent += "del"
                offset -= 1
            else:
                after_sent += prev_token
            if idx > 0:
                after_sent += " "
            prev_token = all_tokens[idx]
            idx += 1

        return after_sent, offset
