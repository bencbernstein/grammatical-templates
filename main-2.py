from modules.grammatical_templates import *
from modules.data import *
from modules.pdf_converter import *
import numpy as np
import textwrap
import pdfminer

texts = open("texts/demons.txt").read()

#mythology_text = convert_pdf_to_txt("texts/[Mike_Dixon-Kennedy]_Encyclopedia_of_Greco-Roman_Mythology.pdf")
demon_text = convert_pdf_to_txt("texts/The Encyclopedia of Demons and Demonology.pdf")

#=== set text ===
texts = demon_text
# ==== # ====

# divide long texts into pieces for spacy
texts = textwrap.wrap(texts, len(texts) / 4)

#test data
#texts = ["Andrealphus is a mighty marquis, who rules 30 LEGIONs. He ﬁrst appears as a noisy peacock and then as a human."]
multiple_is_test = ["Adramalech is the grand chancellor of DEMONs, president of the DEVIL’s general council, and governor of the somethings.", "Adramelch is the grand chancellor of Demons, but not a king himself.", "Adramelch is the grand chancellor of the demons, but not a king himself, although he is president of the Devil's general council."]


# TODO - remap these as conditionals, ex certain objects only work for certain predicates
params = {
    "subject_dependencies": ["nsubj", "nsubjpass"],
    # "subject_required_POS": ["PROPN"],
    # list data options = demons, gods
    "subject_must_contain": demons,
    "object_dependencies": ["npadvmod", "attr", "acomp", "dobj", "pobj", "oprd"],
    "predicate_dependencies": ["ROOT"],
    "predicate_verbs": ["be", "receive", "teach", "appear", "known", "ride", "carry", "worship", "summon"],
    "debug" : False 
}

triples = get_triples(texts, params)

output_to_csv(triples, filename="csvs/demon-triples-dec-20.csv")
