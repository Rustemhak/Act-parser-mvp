from pdf2docx import Converter


def merge_t(tables: list) -> list:
    result = []
    headers7 = ['Дата последн. Перфорации', 'Дата изоляции', 'Горизонт', 'Пласт', 'Интервал, м',
                'Перфоратор', 'Назначение перфорации', 'Расч.пл отность отв/м', 'Накоп.к ол-во отв']
    headers16 = ['Код вида работы', 'Материал (реагент)', 'Плотно сть г/см3']
    headers17 = ['Стоимость работ, руб', 'Продолжительность, час', 'ЦКО', 'сметная', 'фактическая', 'плановая',
                 'фактическая']
    header7 = False
    header16 = False
    header17 = False
    merge1 = False
    merge2 = False

    for table in tables:

        for header in headers7:
            if len(table[0]) == 11 and header in table[0]:
                header7 = True
                break

        for header in headers16:
            if header7 and len(table[0]) == 9 and header in table[0]:
                header16 = True
                break

        for header in headers17:
            if header16 and header in table[0]:
                header17 = True
                break

        if header7 and (not header16) and merge1:
            result[-1] += table

        elif header7 and (not header16):
            merge1 = True
            result.append(table)

        elif header16 and (not header17) and merge2:
            result[-1] += table

        elif header16 and (not header17):
            merge2 = True
            result.append(table)

        else:
            result.append(table)

    return result


if __name__ == "__main__":
    cv = Converter('Технология МГС-К/AKT_KRS_2958_АЗН.pdf')
    tables = cv.extract_tables()
    cv.close()
    merged_tables = merge_t(tables)
    for table in merged_tables:
        for row in table:
            print(row)
        print('\n\n\n')
