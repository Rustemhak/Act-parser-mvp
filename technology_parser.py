import pdfplumber
from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline
from yargy import rule, and_, Parser, or_
from yargy.predicates import is_capitalized, gte, lte, eq
from collections import defaultdict
import pandas as pd
from yargy_utils import NUMERO_SIGN, INT, show_json, ADJF, SLASH, COLON, TOKENIZER, ADJS, DECIMAL, PERCENT
from feature_volume_percent import extract_volumes_feature_percents, count_sum_volume
from water_squeezing import extract_water_volumes


class Match(object):
    def __init__(self, fact, spans):
        self.fact = fact
        self.spans = spans


class Extractor(object):
    def __init__(self, MAIN_FIELD, OTHER_FIELDS=None):
        self.left_parser = Parser(MAIN_FIELD, tokenizer=TOKENIZER)
        if OTHER_FIELDS is not None:
            self.right_parser = Parser(OTHER_FIELDS, tokenizer=TOKENIZER)

    def __call__(self, line):
        """
        Извлекает значение параметра между названиями полей
        :param line: строка
        :return: значение параметра
        """
        left_matches = self.left_parser.findall(line)
        left_spans = [_.span for _ in left_matches]
        right_matches = self.right_parser.findall(line)
        right_spans = [_.span for _ in right_matches]
        if left_spans and right_spans:
            return line[left_spans[0].stop:right_spans[0].start].strip()


def show_from_act(my_rule, lines):
    parser = Parser(my_rule)
    matches = list(parser.findall(lines))
    if matches:
        match = matches[0]
        fact = match.fact
        show_json(fact.as_json)


def get_field_value(my_rule, lines):
    parser = Parser(my_rule)
    matches = list(parser.findall(lines))
    if matches:
        match = matches[0]
        fact = match.fact
        return fact


def get_field_value_second(my_rule, lines):
    parser = Parser(my_rule)
    for line in lines:
        line = line.strip()
        match = list(parser.findall(line))
        if line is not None and len(line) and len(match):
            fact = match[0].fact
            fact.value = line.replace(fact.field_name, '').strip(' .')
            ## print('fact', fact)
            return fact


def get_field_by_prev_rule(def_rule, extra_def_rule, val_rule, lines, idx_forward=3, checked=[]):
    parser = Parser(def_rule)
    extra_parser = Parser(extra_def_rule)
    idx_val = None
    for i, line in enumerate(lines):
        line = line.strip()
        match = list(parser.findall(line))
        extra_match = list(extra_parser.findall(line))
        if line is not None and len(line) and len(match) and len(extra_match):
            idx_val = i
            break
    parser = Parser(val_rule)
    facts = []
    if idx_val is not None:
        checked.append(idx_val)
    if idx_val is None:
        print()
        return [], []
    for idx in range(idx_val + 1, idx_val + idx_forward + 1):
        line = lines[idx].strip()
        match = list(parser.findall(line))
        if line is not None and len(line) and len(match):
            fact_local = match[0].fact
            fact_local.value = line.replace(fact_local.field_name, '').strip(' .')
            ## print('fact', fact)
            facts.append(fact_local)
    return facts, checked


def get_field_by_prev_rule_with_value(def_rule, val_rules, lines, checked, idx_forward=1):
    parser = Parser(def_rule)
    idx_val = None
    for i, line in enumerate(lines):
        line = line.strip()
        match = list(parser.findall(line))
        if line is not None and len(line) and len(match) and i not in checked:
            idx_val = i
            checked.append(i)
            break
    facts = []
    for idx in range(idx_val, idx_val + idx_forward + 1):
        line = lines[idx].strip()
        for val_rule in val_rules:
            parser = Parser(rule(val_rule))
            match = list(parser.findall(line))
            if line is not None and len(line) and len(match):
                fact_ = match[0].fact
                ## print('fact', fact)
                # return fact, checked
                facts.append(fact)
    return facts, checked


def get_MGSK(data, path):
    # Чтение
    pdf = pdfplumber.open(path)
    pages = pdf.pages
    text_act = '\n'.join([page.extract_text(
        layout=True,
        use_text_flow=True) for page in pages])
    lines = text_act.split('\n')
    print(text_act)
    # Скважина
    WELL_WORD = morph_pipeline(['Скв'])
    Well = fact(
        'Well',
        ['field_name', 'value']
    )
    WELL = rule(rule(WELL_WORD, NUMERO_SIGN).interpretation(Well.field_name)).interpretation(Well)
    result = get_field_value_second(WELL, lines)
    data["Скважина"].append(result.value)
    # Скорости насыщения
    SATURATION = morph_pipeline(['насытить'])
    THROTTLE_RESPONSE = morph_pipeline(['приемистость'])

    Speed_Throttle_response = fact(
        'Speed_Throttle_response',
        ['field_name', 'value']
    )
    NUMBER_SPEED = morph_pipeline(['1', '2', '3'])
    SPEED = morph_pipeline(['скорость'])
    SPEED_THROTTLE_RESPONSE = rule(
        rule(NUMBER_SPEED, SPEED, COLON).interpretation(Speed_Throttle_response.field_name)).interpretation(
        Speed_Throttle_response)
    print('path:', path)
    checked = []

    facts_speed_throttle_response, checked = get_field_by_prev_rule(SATURATION, THROTTLE_RESPONSE,
                                                                    SPEED_THROTTLE_RESPONSE,
                                                                    lines)
    if len(facts_speed_throttle_response) == 0:
        data["Комментарий"].append("Скорости не найдены - описание сильно отличается")
    # Приемистость скважины на 1-й скорости
    for fact_speed_throttle_response in facts_speed_throttle_response:
        if fact_speed_throttle_response.field_name[0] == '1':
            data["Приемистость скважины на 1-й скорости"].append(fact_speed_throttle_response.value)
            break

    # Приемистость скважины на 2-й скорости
    for fact_speed_throttle_response in facts_speed_throttle_response:
        if fact_speed_throttle_response.field_name[0] == '2':
            data["Приемистость скважины на 2-й скорости"].append(fact_speed_throttle_response.value)
            break
    # Приемистость скважины на 3-й скорости
    for fact_speed_throttle_response in facts_speed_throttle_response:
        if fact_speed_throttle_response.field_name[0] == '3':
            data["Приемистость скважины на 3-й скорости"].append(fact_speed_throttle_response.value)
    """
    Объем закачки на первой стадии
    концентрация ПАА на первой стадии
    концентрация ПАВ на первой стадии
    концентрация СА (СКА) на первой стадии
    концентрация ХКК на первой стадии

    Объем закачки на второй стадии
    концентрация ПАА на второй стадии
    концентрация ПАВ на второй стадии
    концентрация СА (СКА) на второй стадии
    концентрация ХКК на второй стадии
    """

    facts_features = extract_volumes_feature_percents(text_act)
    WHICH_STAGE = ['первой', 'второй']
    idx_stage = -1
    volumes = []
    field_names = [fact_feature.field_name for fact_feature in facts_features]
    print(facts_features)
    data['Количество стадий закачки'].append(field_names.count('объём'))
    if field_names.count('объём') > 2:
        data['Комментарий'].append(
            f"количество стадий больше двух, а именно {field_names.count('объём')}")
    for fact_feature in facts_features:
        if fact_feature.field_name == 'объём' and idx_stage < 1:
            idx_stage += 1
            volume = fact_feature.value.replace(' ', '')
            volumes.append(volume)
            data[f'Объем закачки на {WHICH_STAGE[idx_stage]} стадии'].append(volume)
        elif fact_feature.field_name == 'объём' and idx_stage == 1:
            break
        elif fact_feature.field_name == 'ПАА':
            data[f'концентрация ПАА на {WHICH_STAGE[idx_stage]} стадии'].append(fact_feature.value)
        elif fact_feature.field_name == 'ПАВ':
            data[f'концентрация ПАВ на {WHICH_STAGE[idx_stage]} стадии'].append(fact_feature.value)
        elif fact_feature.field_name in ['СА', 'СКА']:
            data[f'концентрация СА (СКА) на {WHICH_STAGE[idx_stage]} стадии'].append(fact_feature.value)
        elif fact_feature.field_name == 'ХКК':
            data[f'концентрация ХКК на {WHICH_STAGE[idx_stage]} стадии'].append(fact_feature.value)
    """
    Количество стадий закачки
    Значение по умолчанию 2
    """
    data['Общий объем закачки МГС-К'].append(count_sum_volume(volumes))

    # Давление закачки
    INJECTION_PRESSURE_SIGN = morph_pipeline(['Рзак='])
    PRESSURE_UNIT = rule(rule(INT, eq('-')).repeatable().optional(), INT, morph_pipeline(['атм']))
    Injection_pressure = fact('Injection_pressure',
                              ['field_name', 'value']
                              )
    INJECTION_PRESSURE = rule(INJECTION_PRESSURE_SIGN.interpretation(Injection_pressure.field_name),
                              PRESSURE_UNIT.interpretation(Injection_pressure.value)).interpretation(Injection_pressure)
    fact_injection_pressure = get_field_value(INJECTION_PRESSURE, text_act)
    if fact_injection_pressure is not None:
        data['Давление закачки'].append(fact_injection_pressure.value)

    # Общий объем закачки  МГС-К
    # после закачки
    """
    Объем продавки после первой фазы
    Объем финальной продавки
    """
    facts_squeezing = extract_water_volumes(text_act)
    SQUEEZING_NAMES = ['Объем продавки после первой фазы',
                       'Объем финальной продавки']
    print('количество продавок в тексте: ', len(facts_squeezing))
    print(facts_squeezing)
    for i, fact_squeezing in enumerate(facts_squeezing[:2]):
        data[SQUEEZING_NAMES[i]].append(fact_squeezing.value)

    """
    Вторые скорости
    """
    INJECTION = morph_pipeline(['продавить', 'приемистость'])
    THROTTLE_RESPONSE = morph_pipeline(['приемистость'])
    Speed_injection = fact(
        'Speed_injection',
        ['field_name', 'value']
    )
    NUMBER_SPEED = morph_pipeline(['1', '2', '3'])
    SPEED = morph_pipeline(['скорость'])
    SPEED_INJECTION = rule(
        rule(NUMBER_SPEED, SPEED, COLON).interpretation(Speed_injection.field_name)).interpretation(
        Speed_injection)
    facts_speed_injection, checked = get_field_by_prev_rule(INJECTION, THROTTLE_RESPONSE, SPEED_INJECTION, lines,
                                                            checked=checked)
    print(facts_speed_injection)
    # Приемистость скважины на 1-й скорости после закачки
    # Приемистость скважины на 2-й скорости после закачки
    # Приемистость скважины на 3-й скорости после закачки
    for fact_speed_injection in facts_speed_injection:
        if fact_speed_injection.field_name[0] == '1':
            data["Приемистость скважины на 1-й скорости после закачки"].append(fact_speed_injection.value)
            break

    # Приемистость скважины на 2-й скорости
    for fact_speed_injection in facts_speed_injection:
        if fact_speed_injection.field_name[0] == '2':
            data["Приемистость скважины на 2-й скорости после закачки"].append(fact_speed_injection.value)
            break
    # Приемистость скважины на 3-й скорости
    for fact_speed_injection in facts_speed_injection:
        if fact_speed_injection.field_name[0] == '3':
            data["Приемистость скважины на 3-й скорости после закачки"].append(fact_speed_injection.value)
            break

    # Согласовано
    AGREED = morph_pipeline(['Cогласовано', 'по согласованию'])
    parser_agreed = Parser(AGREED)
    matches = list(parser_agreed.findall(text_act))
    if len(matches) > 0:
        data['Согласовано'].append('Да')
    else:
        data['Согласовано'].append('Нет')

    return data


if __name__ == '__main__':
    path = 'AKT_KRS_2318_АН.pdf'
    data = defaultdict(list)
    data = get_MGSK(path, data)
    df = pd.DataFrame(data=data)
    df.to_excel("таблица_МГС-К.xlsx")
