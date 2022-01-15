# !/bin/sh

#  filter_dict.py
#  
#
#  Created by Eleanor Chodroff on 2/22/15.
# This script filters out words which are not in our corpus.
# It requires a list of the words in the corpus: words.txt

# Ahmad Naufal Hakim - adjust script
# so that it creates lexicon of all
# words (not only what present in
# training data, but also test data).
# Write it into data/local/lang/lexicon.txt
# with an additional entry "<oov> <oov>"

import os
import re

ref = dict()
phones = dict()

duplicate_word_regex = re.compile(r'\(\d+\)')

with open("../../../lexicon") as f, open("lexicon.txt", "w") as lex :
    lex.write("<oov> <oov>\n")
    for line in f:
        line = line.strip()
        columns = line.split()
        if duplicate_word_regex.search(columns[0]) is None :
            word = columns[0]
            pron = " ".join(columns[1:])
            lex.write(word + " " + pron + "\n")