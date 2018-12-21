import spacy
import csv
from pprint import pprint

def set_custom_boundaries(doc):
    for token in doc[:-1]:
        if token.pos_ in "CCONJ" or token.text in [";", ":"]:
            doc[token.i+1].is_sent_start = True
    return doc

def sentence_and_context(index, sentences, subject, object_, predicate):
    l = len(sentences)
    sentence = " ".join([token.text for token in sentences[index]])
    formatted_sentence = sentence.lower()
    #formatted_sentence = formatted_sentence.replace(subject.lower(), subject.upper())
    #.replace(object_.lower(), object_.upper()).replace(predicate.lower(), predicate.upper()) ### not working for some reason

    if index > 0:
        previous =  " ".join([token.text for token in sentences[index - 1]])
    else:
        previous = " (no previous sentence)"
    if index < (l - 1):
        next_ = " ".join([token.text for token in sentences[index + 1]])
    else:
        next_ = " (no next sentence)"
    return previous.lower() + "===" + formatted_sentence + "===" + next_.lower()

def subtree(token, doc):
    return " ".join([token.text for token in doc[token.left_edge.i: token.right_edge.i + 1]])

def subtree_tokens(token, doc):
    return [token for token in doc[token.left_edge.i: token.right_edge.i + 1]]

#def subtree_contains_concept(token, doc, params):

def find_subject(sentence, params, doc, most_recent_subject):
    for token in sentence:
        if token.dep_ in params["subject_dependencies"]: # and subtree_contains_concept(token, doc, params):
            for new_token in subtree_tokens(token,doc):
                if new_token.text.lower() in params["subject_must_contain"]:
                    return {"subject": token, "subject_tree": subtree(token,doc)}
            
            # if it's a pronoun and no concept found in subtree, use most recent subject if it's a personal pronoun
            for new_token in subtree_tokens(token, doc):
                personal_pronouns = ["he", "she", "her", "he"]
                if new_token.pos_ == "PRON" and len(most_recent_subject) > 2 and new_token.text in personal_pronouns:
                    return {"subject": token, "subject_tree": most_recent_subject + " (" + token.text + ")"}

def find_object(sentence, params, subject_token, doc):
    for token in sentence:
        # object should never be in the subject subtree. 
        if token.dep_ in params["object_dependencies"] and token not in subtree_tokens(subject_token, doc):
            return {"object_": token, "object_tree": subtree(token, doc)}

def prepositions(token, sentence, doc):
    rights = []
    # only get rights with no space between root and token
    for token in doc[token.i + 1:sentence.end]:
        if token.dep_ in ["prep", "neg", "advmod"]: 
            rights.append(token.text)
        else:
            break
    return " ".join(rights)

def aux_verbs(token, doc):
    aux_verbs = " ".join([token.text for token in doc[token.i].lefts if token.dep_ in ["aux", "auxpass"]])
    return aux_verbs

def find_predicate(sentence, params, doc):
    for token in sentence:
        if token.dep_ in params["predicate_dependencies"] and token.lemma_ in params["predicate_verbs"]:
            return {"predicate": token, "predicate_tree" : aux_verbs(token, doc) + " " +  token.text + " " + prepositions(token, sentence, doc)}
                
def parse_tree(sentence):
    return "\n".join([(token.text + " | " + token.dep_ + " | " + token.pos_ + " | [" + ", ".join([child.text for child in token.children]) + "]") for token in sentence])
        
def last_search_term(sentence, params):
    last_search_term = ""
    for token in sentence:
        if token.text in params["subject_must_contain"]:
            last_search_term = token.text
    if len(last_search_term) > 2:
        return last_search_term

def get_triples(texts, params):
    nlp = spacy.load('en_core_web_lg')
    #nlp.add_pipe(set_custom_boundaries, before='parser')
    triples = []

    number_of_text_chunks = len(texts)
    most_recent_subject = ""

    for index, text in enumerate(texts):
        print("examining text chunk", index + 1, "/", number_of_text_chunks)
        doc = nlp(text)

        for index, sentence in enumerate(doc.sents):

            print("examining sentence", index, "/", len(list(doc.sents)), end='\r')
            triple = {}
            triple["parse_tree"] = parse_tree(sentence)

            # MUST BE IN SUBJECT, PREDICATE, OBJECT ORDER 

            subject_data = find_subject(sentence, params, doc, most_recent_subject)
            if subject_data:
                triple["subject"] = subject_data["subject"]
                triple["subject_tree"] = subject_data["subject_tree"]
 
                # truncate sentence after subject
                truncated_sentence = doc[triple["subject"].i + 1:sentence.end]

                predicate_data = find_predicate(truncated_sentence, params, doc)
                if predicate_data:
                    triple["predicate"] = predicate_data["predicate"]
                    triple["predicate_tree"] = predicate_data["predicate_tree"]

                    # truncate sentence after predicate
                    truncated_sentence = doc[triple["predicate"].i + 1:sentence.end]
                    
                    object_data = find_object(truncated_sentence, params, triple["subject"], doc)
                    if object_data:
                        triple["object_"] = object_data["object_"]
                        triple["object_tree"] = object_data["object_tree"]

                        triple["sentence"] = sentence_and_context(index, list(doc.sents), triple["subject"], triple["object_"], triple["predicate"])
                        triples.append(triple)
            
            # get the last proper noun in the sentence to save as most recent subject, if there is one
            if last_search_term(sentence, params):
                most_recent_subject = last_search_term(sentence, params)
            
    return triples

def output_to_csv(dataArray, filename):
    headers = ["subject_tree", "object_tree", "predicate_tree", "sentence", "parse_tree", "subject", "object_", "predicate"]
    with open(filename, 'w') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(headers)
        for row in dataArray:
            formatted_row = []
            for header in headers:
                formatted_row.append(row[header])
            writer.writerow(formatted_row)
    print("finished CSV output")
