#pip install ipympl

import re
import pdfplumber
from collections import namedtuple
import tkinter
import pandas as pd
import numpy as np
import matplotlib 
import matplotlib.pyplot as plt
import os
import seaborn as sns
from datetime import datetime
import locale

def extract_text_segments(pdf_path):
        text_segment_list = []

        with pdfplumber.open(pdf_path) as pdf:
            # Iterate through all pages in the PDF
            for page_number in range(len(pdf.pages)):
                # Access the specific page (page_number because page numbers are zero-indexed)
                page = pdf.pages[page_number]

                # Extract text from the page
                text = page.extract_text()

                # Split the text based on the specified expression
                split_expression = "DATA DI RIFERIMENTO:"
                text_segments = text.split(split_expression)

                # Iterate through text segments and add them to the list
                for i, segment in enumerate(text_segments[:-1]):
                    text_segment_list.append(segment.strip())

                # Add the last text segment to the list (if any)
                if text_segments:
                    text_segment_list.append(text_segments[-1].strip())

        return text_segment_list
def extract_numbers_after_zero(text, section_name):
    # Use a regular expression to find the first zero and extract the three numbers after it
    matches = re.finditer(fr'{section_name}.*?0.*?(\d+(?:\.\d+)*(?:\.\d+)?)\D+(\d+(?:\.\d+)*(?:\.\d+)?)\D+(\d+(?:\.\d+)*(?:\.\d+)?)', text)

    result = []
    for match in matches:
        # Extract the numbers
        numbers = [int(match.group(i).replace('.', '')) for i in range(1, 4)]
        result.append(numbers)

    return result
def extract_intermediario_names(text):
        # Use a regular expression to find all occurrences of "Intermediario:" and their corresponding names
        matches = re.finditer(r'Intermediario:\s(.+?)\n', text)
        
        intermediario_names = [match.group(1) for match in matches] if matches else [None]

        return intermediario_names
def extract_intermediario_section(text):
    # Use a regular expression to find the section between "Intermediario:" and the next "Intermediario:" or end of string
    matches = re.finditer(r'Intermediario:(.+?)(?=(Intermediario:|$))', text, re.DOTALL)
    
    sections = [match.group(1).strip() for match in matches] if matches else [None]

    return sections
def italian_date_to_datetime(italian_date):
    # Set the Italian locale
    locale.setlocale(locale.LC_TIME, 'it_IT')
    
    # Specify the format of the Italian date string
    italian_date_format = "%B %Y"
    
    # Convert the string to a datetime object
    date_object = datetime.strptime(italian_date, italian_date_format)
    
    # Reset the locale to the default
    locale.setlocale(locale.LC_TIME, '')
    
    return date_object
def create_df_from_pdf(pdf_path):

    # Replace 'your_pdf_file.pdf' with the path to your PDF file
    #pdf_path = file

    resulting_text_segments = extract_text_segments(pdf_path)


    # Create a list to store DataFrames along with Intermediario names
    dataframes_and_names_list = []

    # Process each resulting_text_segment separately
    for example_text in resulting_text_segments:
        # Extract Intermediario names
        intermediario_names = extract_intermediario_names(example_text)

        # Extract sections based on "Intermediario:"
        intermediario_sections = extract_intermediario_section(example_text)

        # Process each section separately
        for i, section_text in enumerate(intermediario_sections):
            section_names = ["RISCHI AUTOLIQUIDANTI", "RISCHI A SCADENZA", "RISCHI A REVOCA"]

            # Create a list of dictionaries, each representing a row
            rows_list = []

            # Extract numbers for each section
            for section_name in section_names:
                numbers_list = extract_numbers_after_zero(section_text, section_name)

                # Determine the maximum length of the arrays
                max_length = max(len(numbers_list), 1)  # 1 for the single Intermediario section

                for j in range(max_length):
                    row_dict = {"Section Name": section_name, "Intermediario Name": intermediario_names[i]}
                    
                    if j < len(numbers_list):
                        row_dict.update({f"Number {k + 1}": numbers_list[j][k] for k in range(3)})
                    else:
                        row_dict.update({f"Number {k + 1}": float('nan') for k in range(3)})
                    
                    rows_list.append(row_dict)

            # Create the DataFrame from the list of dictionaries
            df = pd.DataFrame(rows_list)

            # Drop rows with NaN values
            df = df.dropna()

            # Add a new column with the first two words of the string repeated for each row
            first_two_words = ' '.join(example_text.split()[:2])
            df['First Two Words'] = first_two_words

            # Append the dataframe and Intermediario name to the list
            dataframes_and_names_list.append({"Intermediario Name": intermediario_names[i], "DataFrame": df})

    # Now, dataframes_and_names_list contains DataFrames and corresponding Intermediario names
    # Assuming dataframes_and_names_list is already created

    # Extract DataFrames from the list
    dataframes_list = [item["DataFrame"] for item in dataframes_and_names_list]

    # Concatenate DataFrames along rows
    final_df = pd.concat(dataframes_list, ignore_index=True)

    new_column_names = ['Categoria', 'Intermediario', 'Accordato', 'Accordato Operativo',
        'Utilizzato', 'Periodo']

    df = final_df.rename(columns=dict(zip(final_df.columns, new_column_names)))

    df['Accordato'] = df['Accordato'].astype(int)
    df['Accordato Operativo'] = df['Accordato Operativo'].astype(int)
    df['Utilizzato'] = df['Utilizzato'].astype(int)

    # Now df has new column names
    return df