from pdf2docx import Converter


def get_values_8_10(pdf_file):
    cv = Converter(pdf_file)
    tables = cv.extract_tables(start=0, end=2)
    cv.close()

    # for table in tables:
    #     print(table)
    """
    Вид работы
    Метод работы
    Причина ремонта
    """
    FIELDS_8_10 = ['Код вида работы',
                   'Вид работы',
                   'Код метода работы',
                   'Метод работы',
                   'Причина ремонта',
                   'Код метода работы']

    idx_values = [0, 1, 3, 4, 5]
    values_8_10 = []
    for i in idx_values:
        values_8_10.append([tables[1][2][i].strip()])

    data_8_10 = dict(zip(FIELDS_8_10, values_8_10))
    table11_17 = tables[5]
    table18_28 = tables[6] if len(tables) > 6 else []
    return data_8_10, table11_17, table18_28
