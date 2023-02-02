import os
import openpyxl
from act_from_text import get_info_from_text
from openpyxl.utils import get_column_letter
from openpyxl.worksheet import worksheet
from openpyxl.styles import Font, Fill, PatternFill, NamedStyle, Side, Border, Color
from openpyxl.worksheet.dimensions import ColumnDimension


def set_border(ws, cell_range):
    thin = Side(border_style="thin", color="000000")
    for row in ws[cell_range]:
        for cell in row:
            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)


def set_color(ws, cell_range):
    for row in ws[cell_range]:
        for cell in row:
            cell.font = Font(color="00FF0000")


def create_xlsx(path, data_samples):
    """
    Создание xlsx файла и запись в него
       Редактирую таблицу
    - двигаю данные
    - добавляю колонки и строки
    - записываю данные в ячейки
    https://openpyxl.readthedocs.io/en/stable/editing_worksheets.html
    """
    # создаю книгу
    book = openpyxl.Workbook()

    # по умолчанию создается с таблицей Sheet
    # print(book.sheetnames)
    book.remove(book.active)
    # создаю таблицы
    name_sheet = "Общая информация"
    sheet = book.create_sheet(name_sheet)

    # print(data_samples)
    for row in data_samples:  # получаю данные
        book.guess_types = True
        sheet.append(row)  # записываю данные в строки таблицы
    sheet.insert_rows(0, amount=2)
    sheet["B1"].value = name_sheet.upper()
    sheet["B1"].font = Font(bold=True)

    sheet.column_dimensions["B"].width = 70  # прим. колво символов
    sheet.column_dimensions["C"].width = 60
    set_border(sheet, "B3:C14")
    set_color(sheet, "A3:A14")

    # РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ СКВАЖИНЫ
    sheet.insert_rows(15, amount=3)
    sheet["B16"].value = 'РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ СКВАЖИНЫ'
    sheet["B16"].font = Font(bold=True)

    # РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ СКВАЖИНЫ
    # sheet.insert_rows(21, amount=4)
    # sheet["B23"].value = 'ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ'
    # sheet["B23"].font = Font(bold=True)

    path_result = f'Таблицы/{path[:-3]}xlsx'
    os.makedirs(os.path.dirname(path_result), exist_ok=True)
    book.save(path_result)
    # book = openpyxl.load_workbook(path_result)
    # sheet = book.active
    # sheet = book[name_sheet]
    # col = sheet.column_dimensions['A']
    # col.font = Font(color="00FF00")
    # book.save(path_result)
    return path_result


if __name__ == '__main__':
    with open('path_directory.txt', encoding='utf-8', mode='r') as f:
        directory = f.readline()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                path_file = os.path.join(root, file)
                data = get_info_from_text(path_file)
                create_xlsx(path_file, data)
