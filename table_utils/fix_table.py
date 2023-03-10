def fix_perforation(table: list[list]) -> list[list]:
    table[0][1] = 'Дата последн. Перфорации'
    table[0].insert(2, 'Дата изоляции')
    table[1].insert(0, None)

    for i, row in enumerate(table):
        if i > 1:
            row.insert(2, '')

    return table


if __name__ == '__main__':
    tab = fix_perforation(
        [
            ['В и д', '<NEST TABLE>', 'Горизонт', 'Пласт', 'Интервал, м', None, 'Перфоратор', 'Назначение перфорации', 'Расч.пл отность отв/м', 'Накоп.к ол-во отв'],
            [None, None, None, None, 'верх', 'низ', None, None, None, None],
            ['Д', '13/04/1990 00:00', 'Кыновский ', 'Дкынов. ', '1771', '1772.7', 'ПК-103 ', 'Повторная ', '40', '68'],
            ['Д', '13/04/1990 00:00', 'Кыновский ', 'Дкынов. ', '1772.7', '1775', 'ПК-103 ', 'Повторная ', '40', '92']
        ]
    )

    for rw in tab:
        print(rw)
