#from pptx import Presentation
import glob
import os
import logging
import sys
import re
import json

#================================================#
# SET LOGGING
#================================================#
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)

# set logging handler in file
fileHandler = logging.FileHandler(filename="log/corpus.log", mode="w")
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)

# set logging handler in Console
# consoleHandler = logging.StreamHandler(sys.stdout)
# consoleHandler.setFormatter(formatter)
# consoleHandler.setLevel(logging.ERROR)
# logger.addHandler(consoleHandler)

class PPTExtract:
    #================================================#
    # INSTANCE ATTRIBUTES. The same for each Class Object
    #================================================#
    def __init__(self, field="economics", root_path=""):
        self.field = field
        self.root_path = root_path
        
    #================================================#
    # METHODS
    #================================================#
    
    #------------------------------------------------------------------------------#
    # PROTECTED METHODS
    #------------------------------------------------------------------------------#
    @staticmethod
    def chain_sub(input_string, substitutions):
        # substitutions must be a list of tuples(r'expression_to_be_replaced', 'replacement_string')
        for pattern, replacement in substitutions:
            input_string = re.sub(pattern, replacement, input_string)
        return input_string
    
    #------------------------------------------------------------------------------#
    # INSTANCE METHODS
    #------------------------------------------------------------------------------#
    def write_corpus(self, lang="de"):
        # now clean the body
        # tuple list of patterns that shall be replaced with certain strings
        if lang == "de":
            pat_and_replace=[
                (r"\r\n", ""),
                (r"\n", ""),
                (r"\t", "")
            ]
        else:
            pat_and_replace = [
                (r"\r\n", ""),
                (r"\n", ""),
                (r"\t", ""),
                (r"ä", "ae"),
                (r"ö", "oe"),
                (r"ü", "ue"),
            ]
            
            base_path = self.root_path
            # avoid errors if special characters in file name
            char_set = "(~$)_$#-"
            # make list of items in a directory
            items = os.listdir(base_path)
            logging.info(items)
            # use os.walk() which generates the file names and related directories in a directory tree by walking the tree either top-down or bottom-up.
            # open corpus files and walk through the tree within the respective folder
            file_sent={} # file-sentences dictionary
            with open(f"data/raw_corpus_{self.field}_{lang}.txt", "w", encoding="utf-8") as rf:
                for root, dirs, files in os.walk(base_path):
                    for dir in dirs:
                        subdir = os.path.join(root, dir)
                        for char in char_set:
                            escape_set = subdir + "/*" + glob.escape(char) + "*" + ".pptx"
                            # return list of files with glob.glob(); set recursive to "True" to search in all subdirs
                            for file in (glob.glob(escape_set, recursive=True)):
                                try:
                                    # open ppt-file and get full content
                                    ppt = Presentation(file)
                                    file_name=str(file)
                                    logging.info(f"\n#---------------------------------------------------------------------------------------------------#\nParsed File: {file}\n#---------------------------------------------------------------------------------------------------#\n")
                                except:
                                    logging.info(f"{file} could not be opened.\n")
                                    continue
                                
                                # iterate through slides
                                for slide in ppt.slides:
                                    for shape in slide.shapes:
                                        if hasattr(shape, "text"):
                                            clean_content = self.chain_sub(shape.text, pat_and_replace)
                                            if file_name not in file_sent.keys():
                                                file_sent[file_name] = [clean_content]
                                            else:
                                                file_sent[file_name].append(clean_content)
                                            
                                            # finally, write lines
                                            line_to_write = clean_content
                                            rf.write(line_to_write + "\n")
                                            
                #---------------------------------------------------------------------------------------------------#
                # Write file-sentence-match JSON according to the language which is used in the file, ensuring the right encoding
                if lang == "de":
                    with open(f"data/file_sentence_{self.field}_{lang}.json", "w", encoding="utf-8") as outfile:
                        json.dump(file_sent, outfile, ensure_ascii=False)
                else:
                    with open(f"data/file_sentence_{self.field}_{lang}.json", "w", encoding="utf-8") as outfile:
                        json.dump(file_sent, outfile, ensure_ascii=True)
                #---------------------------------------------------------------------------------------------------#
                
                clean_content_file = open(f"data/clean_corpus_{self.field}_{lang}.txt", "w", encoding="utf-8")
                lines_list = []
                with open(f"data/raw_corpus_{self.field}_{lang}.txt", encoding="utf-8") as c:
                    for line in c:
                        _line = line.strip()
                        lines_list.append(_line + "\n")
                    for l in lines_list:
                        # ignore empty lines
                        if not l.isspace():
                            clean_content_file.write(l)
                clean_content_file.close()

