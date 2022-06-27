import os

MASCULINE = "Masc"
FEMININE = "Fem"
NEUTRAL = "Neut"

NOMINATIVE = "Nom"
ACCUSATIVE = "Acc"
DATIV = "Dat"
GENITIVE = "Gen"

PLURAL = "Plur"
SINGULAR = "Sing"

NORMAL = 1
FOCUS = 2
DIRECT_DEP = 3
INDIRECT_DEP = 4
DIR_SUBJ = 5

IS_AMOD = 6
IS_DIRECT_CASE = 7

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

USED_LANGUAGES = ['spanish']

LANGUAGE_CODES = {
    'english': 'en',
    'czech': 'cs',
    'basque': 'eu',
    'finnish': 'fi',
    'turkish': 'tr',
    'arabic': 'ar',
    'japanese': 'ja',
    'tamil': 'ta',
    'korean': 'ko',
    'marathi': 'mr',
    'urdu': 'ur',
    'telugu': 'te',
    'indonesian': 'id',
    'spanish': 'spa'
}
