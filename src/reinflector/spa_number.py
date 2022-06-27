import json
import re

from conllu import parse_incr
from tqdm import tqdm as tq

from src.reinflector.spa_base import SpaReinflector
from constants import PLURAL, MASCULINE, SINGULAR
from .utils import handle_case_match, swap_number, parse_reinflected_sentence


def string_replace(word, find, replace):
    """
    The function is from: https://github.com/bermi/Python-Inflector/blob/master/rules/spanish.py
    This function returns a copy of word, translating
    all occurrences of each character in find to the
    corresponding character in replace"""
    for idx, find_idx in enumerate(find):
        word = re.sub(find_idx, replace[idx], word)

    return word


def _has_det(node):
    has_det = False
    for child in node.children:
        if child.token['deprel'] == 'det':
            has_det = True
            break
    return has_det


def remove_a(node_id, cur_sent):
    cur_sent[node_id]['form'] = ""
    return True, -1


def add_a(node, cur_sent):
    if "Gender" not in node.token['feats']:
        return False, 0
    gender = node.token['feats']['Gender']
    node_id = node.token['id'] - 1
    after = "un" if gender == MASCULINE else "una"
    cur_sent[node_id]['form'] = after + " " + cur_sent[node_id]['form']
    return True, 1


class SpaNumberReinflector(SpaReinflector):
    irregular_words = {
        u'base': u'bases',
        u'carácter': u'caracteres',
        u'champú': u'champús',
        u'curriculum': u'currículos',
        u'espécimen': u'especímenes',
        u'jersey': u'jerséis',
        u'memorándum': u'memorandos',
        u'menú': u'menús',
        u'no': u'noes',
        u'país': u'países',
        u'referéndum': u'referendos',
        u'régimen': u'regímenes',
        u'sándwich': u'sándwiches',
        u'si': u'sis',  # Nota musical ALERTA: ¡provoca efectos secundarios!
        u'taxi': u'taxis',
        u'ultimátum': u'ultimatos',
    }

    # These words either have the same form in singular and plural, or have no singular form at all
    non_changing_words = [
        u'lunes', u'martes', u'miércoles', u'jueves', u'viernes',
        u'paraguas', u'tijeras', u'gafas', u'vacaciones', u'víveres',
        u'cumpleaños', u'virus', u'atlas', u'sms', u'hummus',
    ]

    def initialize_dicts(self, ud_files):
        super().initialize_dicts(ud_files)
        for ud_file in ud_files:
            data_file = open(ud_file, "r", encoding="utf-8")

            for number_token_list in tq(parse_incr(data_file)):
                for item in number_token_list:
                    if item['feats']:
                        feats = item['feats']
                        if item['upos'] == 'VERB':
                            feats["lemma"] = item['lemma']
                            self.verbs_dict[json.dumps(feats)] = item['form']
                        if item['deprel'] == 'cop':
                            feats["lemma"] = item['lemma']
                            self.cops_dict[json.dumps(feats)] = item['form']

    def add_sentence_to_df(self, sent_id, sent_before):
        cur_number = self.cache.number
        res_dict = {'ID': sent_id, 'focus': self.cache.cur_lemma,
                    'focus ID': self.cache.cur_focus_idx,
                    'focus ID after': self.cache.target_focus_idx,
                    'adj idx': self.cache.cur_adj_idx,
                    'det idx': self.cache.cur_det_idx,
                    "before": parse_reinflected_sentence(sent_before),
                    "before number": self.cache.number, "deprel": self.cache.deprel,
                    'gender': self.cache.cur_gender, "dep tree size": self.cache.dep_tree_size}

        print(sent_id, ": " + parse_reinflected_sentence(self.cache.cur_sent))

        res_dict["after"] = parse_reinflected_sentence(self.cache.cur_sent)
        res_dict["after number"] = swap_number(cur_number)

        self.df.append(res_dict)

        self.cache.reset_values()

    def pluralize(self, word):
        """
        The function is from: https://github.com/bermi/Python-Inflector/blob/master/rules/spanish.py
        Pluralizes Spanish nouns.
        Input string can be Unicode (e.g. u"palabra"), or a str encoded in UTF-8 or Latin-1.
        Output string will be encoded the same way as the input.
        """

        rules = [
            [u'(?i)([aeiou])x$', u'\\1x'],
            # This could fail if the word is oxytone.
            [u'(?i)([áéíóú])([ns])$', u'|1\\2es'],
            [u'(?i)(^[bcdfghjklmnñpqrstvwxyz]*)an$', u'\\1anes'],  # clan->clanes
            [u'(?i)([áéíóú])s$', u'|1ses'],
            [u'(?i)(^[bcdfghjklmnñpqrstvwxyz]*)([aeiou])([ns])$', u'\\1\\2\\3es'],  # tren->trenes
            [u'(?i)([aeiouáéó])$', u'\\1s'],  # casa->casas, padre->padres, papá->papás
            [u'(?i)([aeiou])s$', u'\\1s'],  # atlas->atlas, virus->virus, etc.
            [u'(?i)([éí])(s)$', u'|1\\2es'],  # inglés->ingleses
            [u'(?i)z$', u'ces'],  # luz->luces
            [u'(?i)([íú])$', u'\\1es'],  # ceutí->ceutíes, tabú->tabúes
            [u'(?i)(ng|[wckgtp])$', u'\\1s'],
            # Anglicismos como puenting, frac, crack, show (En que casos podría fallar esto?)
            [u'(?i)$', u'es']  # ELSE +es (v.g. árbol->árboles)
        ]

        lower_cased_word = word.lower()

        for uncountable_word in self.non_changing_words:
            if lower_cased_word[-1 * len(uncountable_word):] == uncountable_word:
                return word

        for irregular_singular, irregular_plural in self.irregular_words.items():
            match = re.search(u'(?i)(^' + irregular_singular + u')$', word, re.IGNORECASE)
            if match:
                result = re.sub(u'(?i)' + irregular_singular + u'$',
                                match.expand(u'\\1')[0] + irregular_plural[1:],
                                word)
                return result

        for rule in rules:
            match = re.search(rule[0], word, re.IGNORECASE)
            if match:
                groups = match.groups()
                replacement = rule[1]
                if re.match(r'\|', replacement):
                    for i in range(1, len(groups)):
                        replacement = replacement.replace(u'|' + str(i),
                                                          string_replace(groups[i - 1],
                                                                         u'ÁÉÍÓÚáéíóú',
                                                                         u'AEIOUaeiou'))

                result = re.sub(rule[0], replacement, word)
                # Esto acentúa los sustantivos que al pluralizarse se
                # convierten en esdrújulos como esmóquines, jóvenes...
                match = re.search(u'(?i)([aeiou]).{1,3}([aeiou])nes$', result)

                if match and len(match.groups()) > 1 and not re.search(u'(?i)[áéíóú]', word):
                    result = result.replace(match.group(0), string_replace(
                        match.group(1), u'AEIOUaeiou', u'ÁÉÍÓÚáéíóú') + match.group(0)[1:])

                return result

        return word

    def singularize(self, word):
        """
        The function is from: https://github.com/bermi/Python-Inflector/blob/master/rules/spanish.py
        Singularizes Spanish nouns.
        Input string can be Unicode (e.g. u"palabras"), or a str encoded in UTF-8 or Latin-1.
        Output string will be encoded the same way as the input.
        """

        rules = [
            [r'(?i)^([bcdfghjklmnñpqrstvwxyz]*)([aeiou])([ns])es$', u'\\1\\2\\3'],
            [r'(?i)([aeiou])([ns])es$', u'~1\\2'],
            [r'(?i)shes$', u'sh'],  # flashes->flash
            [r'(?i)oides$', u'oide'],  # androides->androide
            [r'(?i)(sis|tis|xis)$', u'\\1'],  # crisis, apendicitis, praxis
            [r'(?i)(é)s$', u'\\1'],  # bebés->bebé
            [r'(?i)(ces)$', u'z'],  # luces->luz
            [r'(?i)([^e])s$', u'\\1'],  # casas->casa
            [r'(?i)([bcdfghjklmnñprstvwxyz]{2,}e)s$', u'\\1'],  # cofres->cofre
            [r'(?i)([ghñptv]e)s$', u'\\1'],  # llaves->llave, radiocasetes->radiocasete
            [r'(?i)jes$', u'je'],  # ejes->eje
            [r'(?i)ques$', u'que'],  # tanques->tanque
            [r'(?i)es$', u'']  # ELSE remove _es_  monitores->monitor
        ]

        lower_cased_word = word.lower()

        for uncountable_word in self.non_changing_words:
            if lower_cased_word[-1 * len(uncountable_word):] == uncountable_word:
                return word

        for irregular_singular, irregular_plural in self.irregular_words.items():
            match = re.search(u'(^' + irregular_plural + u')$', word, re.IGNORECASE)
            if match:
                result = re.sub(u'(?i)' + irregular_plural + u'$',
                                match.expand(u'\\1')[0] + irregular_singular[1:],
                                word)
                return result

        for rule in rules:
            match = re.search(rule[0], word, re.IGNORECASE)
            if match:
                groups = match.groups()
                replacement = rule[1]
                if re.match(u'~', replacement):
                    for i in range(1, len(groups)):
                        replacement = replacement.replace(u'~' + str(
                            i), string_replace(groups[i - 1], u'AEIOUaeiou', u'ÁÉÍÓÚáéíóú'))

                result = re.sub(rule[0], replacement, word)
                # Esta es una posible solución para el problema de dobles
                # acentos. Un poco guarrillo pero funciona
                match = re.search(u'(?i)([áéíóú]).*([áéíóú])', result)

                if match and len(match.groups()) > 1 and not re.search(u'(?i)[áéíóú]', word):
                    result = string_replace(
                        result, u'ÁÉÍÓÚáéíóú', u'AEIOUaeiou')

                return result

        return word

    def reinflect_number(self, before, before_number):
        if before_number == PLURAL:
            return self.singularize(before)
        return self.pluralize(before)

    def reinflect_cop(self, cur_sent, node, parent):
        cop_child_num = 0
        for child in parent.children:
            if child.token['deprel'] == 'cop':
                cop_child_num += 1
                return self.reinflect_verb(cur_sent, node, child, is_cop=True)
        if cop_child_num == 0:
            return False, cur_sent

        return False, cur_sent

    def reinflect_verb(self, cur_sent, node, verb_node, is_cop=False):
        if 'feats' not in verb_node.token:
            return True, cur_sent
        if 'Number' not in verb_node.token['feats']:
            return True, cur_sent

        reinflected = verb_node.token['feats'].copy()
        reinflected["lemma"] = verb_node.token['lemma']
        reinflected["Number"] = swap_number(reinflected["Number"])
        reinflected = json.dumps(reinflected)

        before = verb_node.token['form']

        if is_cop:
            target = self.cops_dict
        else:
            target = self.verbs_dict

        if reinflected in target:
            after = target[reinflected]
            after = handle_case_match(before, after)

            node_id = verb_node.token['id'] - 1
            cur_sent[node_id]['form'] = after
            return True, cur_sent
        return False, cur_sent

    def reinflect_noun(self, cur_sent, node, parent):
        if not SpaReinflector.check_if_a_valid_noun(node):
            return False, cur_sent, 0, 0
        before = node.token['form']
        before_number = node.token['feats']['Number']

        after = self.reinflect_number(before, before_number)
        status = True

        if len(after) < 2:  # Dataset problems marking "es" as plural noun!
            return False, cur_sent, 0, 0

        after = handle_case_match(before, after)
        print("NOUN {} -> {}".format(before, after))

        node_id = node.token['id'] - 1
        cur_sent[node_id]['form'] = after

        offset = 0
        if before_number == PLURAL and not _has_det(node):  # add un or una
            new_status, offset = add_a(node, cur_sent)
            status = new_status and status

        return status, cur_sent, node.token['id'] - 1, offset

    def reinflect_adj(self, cur_sent, node, prev_node):
        is_valid, _, _, _ = self.reinflect_noun(cur_sent, node, None)
        return is_valid

    def calc_reinflected_det_pron(self, node):
        reinflected = node.token['feats'].copy()
        reinflected["lemma"] = node.token['lemma']
        reinflected["Number"] = swap_number(reinflected["Number"])
        reinflected = json.dumps(reinflected)

        return reinflected

    def reinflect_det_pron(self, pos, cur_sent, node, prev_node):
        if 'feats' not in node.token or node.token['feats'] is None or "Number" not in \
                node.token['feats']:
            return False, 0

        before = node.token['form']
        node_id = node.token['id'] - 1

        if before in ("un", "una") and \
                node.token['feats']['Number'] == SINGULAR:  # remove a from plurals
            return remove_a(node_id, cur_sent)

        return super().reinflect_det_pron(pos, cur_sent, node, prev_node)


    def reinflect_contraction(self, cur_sent, node, cur_gender):
        return 0
