from pdf2docx import Converter
import logging

logging.basicConfig(filename='myapp.log', filemode='w', level=logging.DEBUG)


def reformat_table_18_28(table):
    columns = ['Вид', 'Дата последн. Перфорации', 'Дата изоляции', 'Горизонт', 'Пласт', 'Интервал, м', None,
               'Перфоратор', 'Назначение перфорации', 'Расч.пл отность отв/м', 'Накоп.к ол-во отв']
    if 'Дата изоляции' in table[0]:
        table[0] = columns
        return table
    logging.warning()
    return [columns]


def format_table(table):
    for i in range(len(table)):
        for j in range(len(table[i])):
            if table[i][j] is not None:
                if isinstance(table[i][j], str):
                    table[i][j] = table[i][j].strip()
                if table[i][j].isdigit():
                    table[i][j] = int(table[i][j])
    return table


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
                   'Причина ремонта']

    idx_values = [0, 1, 3, 4, 5]
    dict_id_fields = dict(zip(idx_values, FIELDS_8_10))
    values_8_10 = []
    for i in idx_values:
        # TODO проверять найден ли параметр
        if tables[1][2][i] is not None:
            values_8_10.append([tables[1][2][i].strip()])
        else:
            logging.warning(f'Не найдено значение {dict_id_fields[i]} в акте {pdf_file}')

    data_8_10 = dict(zip(FIELDS_8_10, values_8_10))
    # таблица ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ
    if len(tables) > 5:
        table18_28 = tables[5]
    else:
        logging.warning(f'Не найдена таблица ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ на первых двух страницах в {pdf_file}')
        table18_28 = [[]]
    # АСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ
    if len(tables) > 6:
        table11_17 = tables[6]
    else:
        logging.warning(f'РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ СКВАЖИНЫ на первых двух страницах в {pdf_file}')
        table11_17 = [[]]
    if 'Код вида работы' not in table11_17[0]:
        table18_28 = table18_28 + table11_17
        if len(tables) > 7:
            table11_17 = tables[7]
        else:
            logging.warning(f'Не найдена таблица РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ СКВАЖИНЫ\
                            на первых двух страницах, \
                а таблица ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ на двух страницах в {pdf_file}')
            table11_17 = [[]]
    table18_28 = reformat_table_18_28(table18_28)
    table18_28 = format_table(table18_28)
    table11_17 = format_table(table11_17)

    return data_8_10, table11_17, table18_28
