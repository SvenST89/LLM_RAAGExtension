# To read the PDF
import PyPDF2
# To analyze the PDF layout and extract text
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure
# To extract text from tables in PDF
import pdfplumber
# To extract the images from the PDFs
from PIL import Image
from pdf2image import convert_from_path
# To perform OCR to extract text from images
import pytesseract 
# To remove the additional created files
import re
import os
import sys
import glob
import logging
import win32api

#================================================#
# SET LOGGING
#================================================#
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')
logger.setLevel(logging.ERROR)

# set logging handler in file
fileHandler = logging.FileHandler(filename="log/pdf.log", mode="w")
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.ERROR)
logger.addHandler(fileHandler)

# set logging handler in Console
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(formatter)
consoleHandler.setLevel(logging.INFO)
logger.addHandler(consoleHandler)

class PDFExtract:
    #################################################
    # COMPUTING SETUP
    #################################################
    
    #================================================#
    # CLASS ATTRIBUTES. The same for each Class Object
    #================================================#
    
    #================================================#
    # INSTANCE ATTRIBUTES. The same for each Class Object
    #================================================#
    def __init__(self, base_path, field):
            
            self.base_path = base_path
            self.field = field
            
            # Parameters Log
            logging.info("##################################################\n")
            logging.info("GIVEN PARAMETERS\n----------------------------------------------------------------------------------------------------------------------------------------------")
            logging.info(f"FOLDER TO SEARCH IN: {self.base_path}")
            logging.info(f"DOMAIN: {self.field}")
            logging.info("##################################################\n")
            
    #================================================#
    # METHODS
    #================================================#
    
    #------------------------------------------------------------------------------#
    # CLASS METHODS
    #------------------------------------------------------------------------------#
    
    #------------------------------------------------------------------------------#
    # PROTECTED METHODS
    #------------------------------------------------------------------------------#
    # These are used inside this class within other methods, 
    # but is not used inside the main code on a class instance level.
    # For building the embedder and the cross encoder we need to
    # call the class "SemanticSearch" in order to address the class attributes.
    
    # Check whether tesseract.exe exists, i.e. is installed. Required for reading image text!
    @staticmethod
    def find_file(root_folder, rex):
        global tesseract_found
        tesseract_found = False
        tesseract_file = None
        for root,dirs,files in os.walk(root_folder):
            for f in files:
                result = rex.search(f)
                if result:
                    tesseract_file = os.path.join(root, f)
                    raw_str = "r" + "'" + tesseract_file + "'"
                    logging.info(f"Tesseract found: {raw_str}")
                    tesseract_found = True
                else:
                    continue # if you want to find only one
                if tesseract_found:
                    break
            if tesseract_found:
                break
        return tesseract_file
    
    #------------------- Create a function to extract text
    @staticmethod
    def text_extraction(element):
        # Extracting the text from the in-line text element
        line_text = element.get_text()

        # Find the formats of the text
        # Initialize the list with all the formats that appeared in the line of text
        line_formats = []
        for text_line in element:
            if isinstance(text_line, LTTextContainer):
                # Iterating through each character in the line of text
                for character in text_line:
                    if isinstance(character, LTChar):
                        # Append the font name of the character
                        line_formats.append(character.fontname)
                        # Append the font size of the character
                        line_formats.append(character.size)
        # Find the unique font sizes and names in the line
        format_per_line = list(set(line_formats))

        # Return a tuple with the text in each line along with its format
        return (line_text, format_per_line)
    
    #------------------- Create a function to crop the image elements from PDFs
    @staticmethod
    def crop_image(element, pageObj):
        # Get the coordinates to crop the image from the PDF
        [image_left, image_top, image_right, image_bottom] = [element.x0,element.y0,element.x1,element.y1] 
        # Crop the page using coordinates (left, bottom, right, top)
        pageObj.mediabox.lower_left = (image_left, image_bottom)
        pageObj.mediabox.upper_right = (image_right, image_top)
        # Save the cropped page to a new PDF
        cropped_pdf_writer = PyPDF2.PdfWriter()
        cropped_pdf_writer.add_page(pageObj)
        # Save the cropped PDF to a new file
        with open('cropped_image.pdf', 'wb') as cropped_pdf_file:
            cropped_pdf_writer.write(cropped_pdf_file)

    #------------------- Create a function to convert the PDF to images
    @staticmethod
    def convert_to_images(input_file):
        images = convert_from_path(input_file)
        image = images[0]
        output_file = "PDF_image.png"
        image.save(output_file, "PNG")

    #------------------- Create a function to read text from images
    @staticmethod
    def image_to_text(image_path):
        # Read the image
        img = Image.open(image_path)
        # Extract the text from the image
        text = pytesseract.image_to_string(img)
        return text

    #------------------- Extracting tables from the page
    @staticmethod
    def extract_table(pdf_path, page_num, table_num):
        # Open the pdf file
        pdf = pdfplumber.open(pdf_path)
        # Find the examined page
        table_page = pdf.pages[page_num]
        # Extract the appropriate table
        table = table_page.extract_tables()[table_num]
        return table

    #------------------- Convert table into the appropriate format
    @staticmethod
    def table_converter(table):
        table_string = ''
        # Iterate through each row of the table
        for row_num in range(len(table)):
            row = table[row_num]
            # Remove the line breaker from the wrapped texts
            cleaned_row = [item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item in row]
            # Convert the table into a string 
            table_string+=('|'+'|'.join(cleaned_row)+'|'+'\n')
        # Removing the last line break
        table_string = table_string[:-1]
        return table_string
    
    #------------------------------------------------------------------------------#
    # INSTANCE METHODS
    #------------------------------------------------------------------------------#
    # FUNCTION TO SET UP TESSERACT ACCORDINGLY
    def setup_tesseract(self, file_name):
        #create a regular expression for the file
        rex = re.compile(file_name)
        for drive in win32api.GetLogicalDriveStrings().split('\000')[:-1]:
            tesseract_file = self.find_file(drive, rex)
            if tesseract_found:
                pytesseract.pytesseract.tesseract_cmd = tesseract_file
                logging.info("Tesseract has been set up for use in program.")
                break
            else:
                raise Exception(f"No tesseract installation found. The file is: {tesseract_file}")
                break
        
    # FUNCTION TO LOOP THROUGH FILE DATA
    def loop_through_files(self, file_path, file_name):
        # Create the dictionary to store information for each page
        text_per_page = {}
        with open(f"data/pdf_corpus_{self.field}.txt", "w", encoding="utf-8") as rf:
            # make individual document for each file
            doc_path = "documents/" + str(file_name) + ".txt"
            with open(doc_path, "w", encoding="utf-8") as docfile:
                for pagenum, page in enumerate(extract_pages(str(file_path))):
                    # create a PDF file object
                    pdfFileObj = open(file_path, 'rb')
                    # create a PDF reader object
                    pdfRead = PyPDF2.PdfReader(pdfFileObj)

                    # Initialize the variables needed for the text extraction from the page
                    pageObj = pdfRead.pages[pagenum]
                    page_text = []
                    line_format = []
                    text_from_images = []
                    text_from_tables = []
                    page_content = []
                    # Initialize the number of the examined tables
                    table_num = 0
                    first_element= True
                    table_extraction_flag= False
                    # Open the pdf file
                    pdf = pdfplumber.open(file_path)
                    # Find the examined page
                    page_tables = pdf.pages[pagenum]
                    # Find the number of tables on the page
                    tables = page_tables.find_tables()


                    # Find all the elements
                    page_elements = [(element.y1, element) for element in page._objs]
                    # Sort all the elements as they appear in the page 
                    page_elements.sort(key=lambda a: a[0], reverse=True)

                    # Find the elements that composed a page
                    for i,component in enumerate(page_elements):
                        # Extract the position of the top side of the element in the PDF
                        pos= component[0]
                        # Extract the element of the page layout
                        element = component[1]

                        # Check if the element is a text element
                        if isinstance(element, LTTextContainer):
                            # Check if the text appeared in a table
                            if table_extraction_flag == False:
                                # Use the function to extract the text and format for each text element
                                # returns a tuple
                                (line_text, format_per_line) = self.text_extraction(element)
                                # Append the text of each line to the page text
                                page_text.append(line_text)
                                # Append the format for each line containing text
                                line_format.append(format_per_line)
                                page_content.append(line_text)
                            else:
                                # Omit the text that appeared in a table
                                pass

                        # Check the elements for images
                        if isinstance(element, LTFigure):
                            # Crop the image from the PDF
                            self.crop_image(element, pageObj)
                            # Convert the cropped pdf to an image
                            self.convert_to_images('cropped_image.pdf')
                            # Extract the text from the image
                            image_text = self.image_to_text('PDF_image.png')
                            text_from_images.append(image_text)
                            page_content.append(image_text)
                            # Add a placeholder in the text and format lists
                            page_text.append('image')
                            line_format.append('image')

                        # Check the elements for tables
                        if isinstance(element, LTRect):
                            lower_side = None
                            upper_side = None
                            # If the first rectangular element
                            if first_element == True and (table_num+1) <= len(tables):
                                # Find the bounding box of the table
                                try:
                                    lower_side = page.bbox[3] - tables[table_num].bbox[3]
                                    upper_side = element.y1
                                except:
                                    pass
                                # Extract the information from the table
                                table = self.extract_table(file_path, pagenum, table_num)
                                # Convert the table information in structured string format
                                table_string = self.table_converter(table)
                                # Append the table string into a list
                                text_from_tables.append(table_string)
                                page_content.append(table_string)
                                # Set the flag as True to avoid the content again
                                table_extraction_flag = True
                                # Make it another element
                                first_element = False
                                # Add a placeholder in the text and format lists
                                page_text.append('table')
                                line_format.append('table')

                            # Check if we already extracted the tables from the page
                            if lower_side == None or upper_side == None:
                                pass
                            elif (element.y0 >= lower_side and element.y1 <= upper_side) or ():
                                pass
                            elif not isinstance(page_elements[i][1], LTRect):
                                table_extraction_flag = False
                                first_element = True
                                table_num+=1


                    # Create the key of the dictionary
                    dctkey = 'Page_'+str(pagenum)
                    # Add the list of list as the value of the page key
                    if dctkey not in text_per_page.keys():
                        text_per_page[dctkey]= [page_text, line_format, text_from_images,text_from_tables, page_content]

                    # finally, write lines
                    text = ''.join(text_per_page[dctkey][4]) # write page_content at index 4
                    docfile.write(text + "\n")
                    rf.write(text + "\n")
                    

                # Closing the pdf file object
                pdfFileObj.close()
                
        return text_per_page
    
    # MAIN METHOD TO WRITE CORPUS AND DICTIONARY OF PARSED FILES
    def write_pdf_corpus_dict(self):
        self.setup_tesseract("tesseract\.exe") # escape the dot for regex.compile()
        # make dictionary to store corpus for each file.
        # Store as keys the "file_name/path" and then the dictionary of pages and text "text_per_page" as value
        file_dict = {}

        # Iterate through the base path and extract all pdfs available
        char_set = "(~$)_$#-"
        for root, dirs, files in os.walk(self.base_path):
            logging.info(f"Parsing from the following base path: {self.base_path}\n")
            # check if dir-list is empty. If yes, then we are inside a folder that only contains files, no directories
            if not dirs:
                logging.info("No directories inside given base path. Browsing through pdf-files only.")
                #for char in char_set:
                    #escape_set = "*" + glob.escape(char) + "*" + ".pdf"
                    #for file_path in (glob.glob(escape_set, recursive=True)):
                for f in files:
                    file_path = os.path.join(root, f)
                    logging.info(f"Current parsed file: {file_path}")
                    text_per_page =  self.loop_through_files(file_path, f)
                    # write all file dictionaries containing file contents into one big dictionary containing
                    # the files as "keys" and the related file content dictionary as "value"
                    file_name = str(file_path)
                    if file_name not in file_dict.keys():
                        file_dict[file_name] = text_per_page
            else:
                logging.info("Base path provides directories and files. Browsing through directories and searching for pdf-files.")
                for dir in dirs:
                    subdir = os.path.join(root, dir)
                    #for char in char_set:
                        #escape_set = subdir + "/*" + glob.escape(char) + "*" + ".pdf"
                        #for file_path in (glob.glob(escape_set, recursive=True)):
                    for f in files:
                        file_path = os.path.join(subdir, f)
                        logging.info(f"Current parsed file: {file_path}")
                        text_per_page =  self.loop_through_files(file_path, f)
                        # write all file dictionaries containing file contents into one big dictionary containing
                        # the files as "keys" and the related file content dictionary as "value"
                        file_name = str(file_path)
                        if file_name not in file_dict.keys():
                            file_dict[file_name] = text_per_page

        # Deleting the additional files created
        #os.remove('cropped_image.pdf')
        #os.remove('PDF_image.png')
        return file_dict