from nltk.corpus import wordnet as wn

from constants import MASCULINE, FEMININE, NEUTRAL, PLURAL, SINGULAR


def handle_case_match(before, after):
    after = after.capitalize()
    if before[0].islower():
        after = after[0].lower() + after[1:]
    return after


def swap_gender(gender_string):
    if gender_string == MASCULINE:
        return FEMININE
    if gender_string == FEMININE:
        return MASCULINE
    return NEUTRAL


def swap_number(number_string):
    if number_string == PLURAL:
        return SINGULAR
    if number_string == SINGULAR:
        return PLURAL
    return NEUTRAL


def parse_reinflected_sentence(token_list):
    after_sent = ""
    for token in token_list:
        if token['form'] != "":
            after_sent += token['form'] + " "
    return after_sent


def sentence_sanity_check(sent_text, tok_list):
    token_str = ""
    for token in tok_list:
        token_str += str(token)
    return token_str == sent_text.replace(" ", "")


def check_if_inanimated(token, lang):
    lemma_synsets = wn.synsets(token['lemma'], lang=lang)
    if not lemma_synsets:
        return False
    for syn in lemma_synsets:
        if wn.synset('person.n.01') in syn.lowest_common_hypernyms(wn.synset('person.n.01')):
            return False
    return True


def check_if_animated(token, lang):
    lemma_synsets = wn.synsets(token['lemma'], lang=lang)
    if not lemma_synsets:
        return False
    if wn.synset('person.n.01') in lemma_synsets[0].lowest_common_hypernyms(
            wn.synset('person.n.01')):
        return True
    return False
