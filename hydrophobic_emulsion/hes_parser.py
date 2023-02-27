import pdfplumber
from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline
from yargy import rule, and_, Parser, or_
from yargy.predicates import is_capitalized, gte, lte, eq
from collections import defaultdict
import pandas as pd

from hydrophobic_emulsion.hes_volume_percent import extract_hes
from hydrophobic_emulsion.time_reaction import extract_time_reaction
from hydrophobic_emulsion.volumes import extract_solution_volumes
from yargy_utils import NUMERO_SIGN, INT, show_json, ADJF, SLASH, COLON, TOKENIZER, ADJS, DECIMAL, PERCENT
from feature_volume_percent import extract_volumes_feature_percents, count_sum_volume, select_text_stages
from water_squeezing import extract_water_volumes, extract_final_water_volumes
from yargy_utils.duration import DURATION


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


def get_field_by_prev_rule(def_rule, extra_def_rule, val_rule, lines, idx_forward=3, checked=None):
    parser = Parser(def_rule)
    extra_parser = Parser(extra_def_rule)
    idx_val = None
    for i, line in enumerate(lines):
        line = line.strip()
        match = list(parser.findall(line))
        extra_match = list(extra_parser.findall(line))
        if line is not None and len(line) and len(match) and len(extra_match) and i not in checked:
            idx_val = i
            break
    parser = Parser(val_rule)
    facts = []
    if idx_val is not None:
        checked.append(idx_val)
    if idx_val is None:
        print()
        return [], [], []
    for idx in range(idx_val + 1, idx_val + idx_forward + 1):
        line = lines[idx].strip()
        match = list(parser.findall(line))
        if line is not None and len(line) and len(match):
            fact_local = match[0].fact
            fact_local.value = line.replace(fact_local.field_name, '').strip(' .')
            ## print('fact', fact)
            facts.append(fact_local)
    facts_volume_final = extract_water_volumes(lines[idx_val])
    return facts, checked, facts_volume_final


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


def check_volumes_solution(volumes):
    return volumes.solution_value == count_sum_volume([volumes.neftenol_value, volumes.water_value])


def get_HES(data, path):
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
    SATURATION = morph_pipeline(['насытить', 'продавить'])
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
    facts_speed_throttle_response, checked, _ = get_field_by_prev_rule(SATURATION, THROTTLE_RESPONSE,
                                                                       SPEED_THROTTLE_RESPONSE,
                                                                       lines, checked=checked)
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
    Объем  продавки
    """
    SQUEEZING_NAMES = ['Объем продавки после первой фазы',
                       'Объем продавки']

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
    facts_speed_injection, checked, facts_squeezing = get_field_by_prev_rule(INJECTION, THROTTLE_RESPONSE,
                                                                             SPEED_INJECTION, lines,
                                                                             checked=checked)
    # facts_squeezing = extract_water_volumes(text_act)

    # print('количество продавок в тексте: ', len(facts_squeezing))
    #
    # print(facts_squeezing)
    # for i, fact_squeezing in enumerate(facts_squeezing[:2]):
    if len(facts_squeezing) > 0:
        data[SQUEEZING_NAMES[1]].append(facts_squeezing[0].value)

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

    """
    Объем первичного раствора	Объем Нефтенола в первичном растворе	Объем воды в первичном растворе
    """
    volumes = extract_solution_volumes(text_act)
    if volumes:
        data['Объем первичного раствора'].append(volumes.solution_value)
        data['Объем Нефтенола в первичном растворе'].append(volumes.neftenol_value)
        data['Объем воды в первичном растворе'].append(volumes.water_value)
        if not check_volumes_solution(volumes):
            data['Комментарий'].append('Опечатка в объёме составляющих раствора')
    """
    Объем ГЭР	Концентрация ПАВ в ГЭР
    """
    hes_volume_percent = extract_hes(text_act)
    if hes_volume_percent:
        data['Объем ГЭР'].append(hes_volume_percent.volume_value)
        data['Концентрация ПАВ в ГЭР'].append(hes_volume_percent.percent_value)
    """
    Время на реагирование
    """
    time_reaction = extract_time_reaction(text_act)
    if time_reaction:
        pretty_time = ''
        if time_reaction.time_value.hours:
            pretty_time += str(time_reaction.time_value.hours) + ' часа '
        if time_reaction.time_value.minutes:
            pretty_time += str(time_reaction.time_value.hours) + ' мин '
        if time_reaction.time_value.seconds:
            pretty_time += str(time_reaction.time_value.hours) + ' сек '

        data['Время на реагирование'].append(pretty_time)
    return data


if __name__ == '__main__':
    path = 'AKT_KRS_2198_АН.pdf'
    data = defaultdict(list)
    data = get_HES(data, path)
    df = pd.DataFrame(data=data)
    df.to_excel("таблица_ГЭР.xlsx")
