from pdf2docx import Converter
import logging
import re

logging.basicConfig(filename='myapp.log', filemode='w', level=logging.DEBUG)


def reformat_table_18_28(table, pdf_file):
    columns = ['Вид', 'Дата последн. Перфорации', 'Дата изоляции', 'Горизонт', 'Пласт', 'Интервал, м', None,
               'Перфоратор', 'Назначение перфорации', 'Расч.пл отность отв/м', 'Накоп.к ол-во отв']
    sub_columns = [None, None, None, None, None, 'верх', 'низ', None, None, None, None]
    if 'Дата изоляции' in table[0]:
        table[0] = columns
        table[1] = sub_columns
        return table
    logging.warning(f'Не найдена таблица ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ на  страницах в {pdf_file}')
    return [columns]


def reformat_table_11_17(table):
    columns = ['Код вида работы', 'Вид работы', 'Материал (реагент)', 'Плотность г / см3', 'Концен трация, % ',
               'Количество',
               'Ед.измерения',
               'Стоимость',
               'Чей реаг 1 - зак2 - исп']
    table[0] = columns
    return table


def add_skip(table):
    for i in range(len(table)):
        for j in range(len(table[i])):
            if table[i][j] == '<NEST TABLE>':
                table[i] = table[i][:j] + ['', ''] + table[i][j + 1:]
    return table


def format_table(table):
    table = add_skip(table)
    for i in range(len(table)):
        for j in range(len(table[i])):
            if table[i][j] is not None:
                if isinstance(table[i][j], str):
                    table[i][j] = table[i][j].strip()
                if table[i][j].isdigit():
                    table[i][j] = int(table[i][j])
                elif re.fullmatch(r'\d+,\d+', table[i][j]):
                    table[i][j] = float(table[i][j].replace(',', '.'))
    return table


def get_values_8_10(pdf_file):
    cv = Converter(pdf_file)
    tables = cv.extract_tables()
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
        if tables[1][2][i] is not None:
            values_8_10.append([tables[1][2][i].strip()])
        elif tables[1][2][i + 1] is not None:
            values_8_10.append([tables[1][2][i + 1].strip()])
        else:
            logging.warning(f'Не найдено значение {dict_id_fields[i]} в акте {pdf_file}')

    data_8_10 = dict(zip(FIELDS_8_10, values_8_10))
    # таблица ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ
    if len(tables) > 5:
        table18_28 = tables[5]
        pass
    else:
        logging.warning(f'Не найдена таблица ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ на страницах в {pdf_file}')
        table18_28 = [[]]
    # РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ
    if len(tables) > 6:
        table11_17 = tables[6]
        pass
    else:
        logging.warning(f'РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ СКВАЖИНЫ на страницах в {pdf_file}')
        table11_17 = [[]]

    if len(table18_28[1]) < 11:
        table18_28 = table18_28[:2] + list(
            map(lambda x: x[0].split(maxsplit=1) + x[1:], table18_28[2:]))
    if 'Код вида' not in table11_17[0][0]:
        table18_28 = table18_28 + table11_17
        if len(tables) > 7:
            table11_17 = tables[7]
        else:
            logging.warning(f'Не найдена таблица РАСХОД МАТЕРИАЛОВ, ИСПОЛЬЗУЕМЫХ ПРИ РЕМОНТЕ СКВАЖИНЫ\
                            на страницах, \
                а таблица ПЕРФОРАЦИЯ, ОТКЛЮЧЕНИЕ ПЛАСТОВ на страницах в {pdf_file}')
            table11_17 = [[]]
    if len(table11_17) > 1 and len(table11_17[1]) < 9 and table11_17[1][0] != '<NEST TABLE>':
        table11_17 = table11_17[:1] + list(
            map(lambda x: x[0].split(maxsplit=1) + x[1:], table11_17[1:]))
    table18_28 = reformat_table_18_28(table18_28, pdf_file)
    table11_17 = reformat_table_11_17(table11_17)
    table18_28 = format_table(table18_28)
    table11_17 = format_table(table11_17)

    return data_8_10, table11_17, table18_28
