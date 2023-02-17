from pdf2docx import Converter
import logging
import re
import os

from act_from_table import reformat_table_11_17, format_table
from merge_tables import merge_t


def extract_materials(pdf_file):
    cv = Converter(pdf_file)
    tables = cv.extract_tables()
    tables = merge_t(tables)
    cv.close()
    # print('количество таблиц',len(tables))
    # print(tables[5])
    tables_materials = tables[6]
    tables_materials = reformat_table_11_17(tables_materials)
    tables_materials = format_table(tables_materials)
    materials = []
    for line in tables_materials[1:]:
        materials.append(line[2:4] + line[5:6])
    return materials


if __name__ == "__main__":
    with open('path_directory.txt', encoding='utf-8', mode='r') as f:
        directory = f.readline()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                path_file = os.path.join(root, file)

                extract_materials(path_file)
