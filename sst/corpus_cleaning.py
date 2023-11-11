import re
import io
#from num2words import num2words
import sys
import os
import pandas as pd

def clean_corpus(file_path, stopword_list=None):
    def chain_sub(input_string, substitutions):
        # substitutions must be a list of tuples(r'expression_to_be_replaced', 'replacement_string')
        for pattern, replacement in substitutions:
            input_string = re.sub(pattern, replacement, input_string)
        return input_string
    
    # Regex Pattern to be replaced
    pat_and_replace=[
        (r"[+*%?!'.;,@ʺ‎…`]", ''),
        (r"(´)", ''),
        (r"(\$)", 's'),
        (r"(<UNK>+)", ''),
        (r"(ñ+)", 'n'),
        (r"(\")", ''),
        (r"(/)", ' '),
        (r"(ş)", 's'),
        (r"(ă)", 'a'),
        (r"(†)", ''),
        (r"(ŭ)", 'u'),
        (r"(ŏ)", 'o'),
        (r"(ō)", 'o'),
        (r"(ī)", 'i'),
        (r"(ç)", 'c'),
        # replace :-
        (r'(:+|-+)', ' '),
        # replace empty spaces with single space
       (r" +", ' '),
            ]
    
    #German_sentences_8mil_filtered_maryfied.txt
    with open(file_path, 'r', encoding='utf-8') as f_input:
        #infile_list=f_input.readlines()[0:int(x)] # returns a list of sentences
        infile_list_rev=[]
        
        # Now check for encoding errors with � symbol and remove these words (to make it simple)
        for sen in f_input:
            wordsplit=re.split(r'\s', sen) # split sentence into list of words
            wordlist=[]
            if stopword_list == None:
                for word in wordsplit:
                    if '�' in word:
                        word="<UNK>"
                        wordlist.append(word)
                    else:
                        if not word.isspace():
                            wordlist.append(word)
            else:
                for word in wordsplit:
                    if '�' in word:
                        word="<UNK>"
                        wordlist.append(word)
                    else:
                        if word not in stopword_list and not word.isspace():
                            wordlist.append(word)
                        else:
                            continue
            joined=' '.join(wordlist)
            infile_list_rev.append(joined)

    with io.open("wip.txt", "w", encoding='utf-8') as wip:
        for item in infile_list_rev:
            wip.write(item + '\n')

    with io.open("wip.txt", 'r', encoding='utf-8') as w_file:
        # open file to work in with .readlines()
        text=w_file.read() # add '.lower()' if you want to make it lowercase
        clean_content = chain_sub(text, pat_and_replace)
        
    with io.open('cleaned.txt', 'w', encoding='utf-8') as f_output:
        f_output.write(text)
    
    #read_file=pd.read_csv('cleaned.txt')
    #read_file.to_csv('data/cleaned.csv', index=None)
    os.remove("wip.txt")