import pdfplumber
from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline
from yargy import rule, and_, Parser, or_
from collections import defaultdict
import pandas as pd
from yargy_utils import (
    NUMERO_SIGN,
    INT,
    show_json,
    ADJF,
    SLASH,
    COLON,
    TOKENIZER,
    ADJS,
    DECIMAL,
    PERCENT,
)
from feature_volume_percent import (
    extract_volumes_feature_percents,
    count_sum_volume,
    select_text_stages,
)
from water_squeezing import extract_water_volumes, extract_final_water_volumes


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
            return line[left_spans[0].stop : right_spans[0].start].strip()


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
            fact.value = line.replace(fact.field_name, "").strip(" .")
            ## print('fact', fact)
            return fact


def get_field_by_prev_rule(
    def_rule, extra_def_rule, val_rule, lines, idx_forward=4, checked=None
):
    parser = Parser(def_rule)
    extra_parser = Parser(extra_def_rule)
    idx_val = None
    for i, line in enumerate(lines):
        line = line.strip()
        match = list(parser.findall(line))
        extra_match = list(extra_parser.findall(line))
        if (
            line is not None and len(line) and len(extra_match) and i not in checked
        ):  # and  len(match)
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
        # замена английской c на русскую с
        line = line.replace("c", "с")
        match = list(parser.findall(line))
        if line is not None and len(line) and len(match):
            fact_local = match[0].fact
            fact_local.value = line.replace(fact_local.field_name, "").strip(" .")
            ## print('fact', fact)
            facts.append(fact_local)
    facts_volume_final = extract_water_volumes(lines[idx_val])
    return facts, checked, facts_volume_final


def get_field_by_prev_rule_with_value(
    def_rule, val_rules, lines, checked, idx_forward=1
):
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
    return volumes.solution_value == count_sum_volume(
        [volumes.neftenol_value, volumes.water_value]
    )


def get_technology(data, path):
    # Чтение
    pdf = pdfplumber.open(path)
    pages = pdf.pages
    text_act = "\n".join(
        [page.extract_text(layout=True, use_text_flow=True) for page in pages]
    )
    lines = text_act.split("\n")
    print(text_act)
    # Скважина
    WELL_WORD = morph_pipeline(["Скв"])
    Well = fact("Well", ["field_name", "value"])
    WELL = rule(
        rule(WELL_WORD, NUMERO_SIGN).interpretation(Well.field_name)
    ).interpretation(Well)
    result = get_field_value_second(WELL, lines)
    try:
        data["Скважина"].append(result.value)
    except:
        data["Скважина"].append("н/д")
    # Скорости насыщения
    SATURATION = morph_pipeline(["насытить", "продавить"])
    THROTTLE_RESPONSE = morph_pipeline(["приемистость"])

    Speed_Throttle_response = fact("Speed_Throttle_response", ["field_name", "value"])
    NUMBER_SPEED = morph_pipeline(["1", "2", "3"])
    SPEED = morph_pipeline(["скорость"])
    SPEED_THROTTLE_RESPONSE = rule(
        rule(NUMBER_SPEED, SPEED, COLON).interpretation(
            Speed_Throttle_response.field_name
        )
    ).interpretation(Speed_Throttle_response)
    print("path:", path)
    checked = []
    facts_speed_throttle_response, checked, _ = get_field_by_prev_rule(
        SATURATION, THROTTLE_RESPONSE, SPEED_THROTTLE_RESPONSE, lines, checked=checked
    )
    if len(facts_speed_throttle_response) == 0:
        data["Комментарий"].append("Скорости не найдены - описание сильно отличается")
    # Приемистость скважины на 1-й скорости
    for fact_speed_throttle_response in facts_speed_throttle_response:
        if fact_speed_throttle_response.field_name[0] == "1":
            data["Приемистость скважины на 1-й скорости"].append(
                fact_speed_throttle_response.value
            )
            break

    # Приемистость скважины на 2-й скорости
    for fact_speed_throttle_response in facts_speed_throttle_response:
        if fact_speed_throttle_response.field_name[0] == "2":
            data["Приемистость скважины на 2-й скорости"].append(
                fact_speed_throttle_response.value
            )
            break
    # Приемистость скважины на 3-й скорости
    for fact_speed_throttle_response in facts_speed_throttle_response:
        if fact_speed_throttle_response.field_name[0] == "3":
            data["Приемистость скважины на 3-й скорости"].append(
                fact_speed_throttle_response.value
            )
    """
    Вторые скорости
    """
    INJECTION = morph_pipeline(["продавить", "приемистость"])
    THROTTLE_RESPONSE = morph_pipeline(["приемистость"])
    Speed_injection = fact("Speed_injection", ["field_name", "value"])
    NUMBER_SPEED = morph_pipeline(["1", "2", "3"])
    SPEED = morph_pipeline(["скорость"])
    SPEED_INJECTION = rule(
        rule(NUMBER_SPEED, SPEED, COLON).interpretation(Speed_injection.field_name)
    ).interpretation(Speed_injection)
    facts_speed_injection, checked, facts_squeezing = get_field_by_prev_rule(
        INJECTION, THROTTLE_RESPONSE, SPEED_INJECTION, lines, checked=checked
    )
    # facts_squeezing = extract_water_volumes(text_act)

    # print('количество продавок в тексте: ', len(facts_squeezing))
    #
    # print(facts_squeezing)
    # for i, fact_squeezing in enumerate(facts_squeezing[:2]):

    print(facts_speed_injection)
    # Приемистость скважины на 1-й скорости после закачки
    # Приемистость скважины на 2-й скорости после закачки
    # Приемистость скважины на 3-й скорости после закачки
    for fact_speed_injection in facts_speed_injection:
        if fact_speed_injection.field_name[0] == "1":
            data["Приемистость скважины на 1-й скорости после закачки"].append(
                fact_speed_injection.value
            )
            break

    # Приемистость скважины на 2-й скорости
    for fact_speed_injection in facts_speed_injection:
        if fact_speed_injection.field_name[0] == "2":
            data["Приемистость скважины на 2-й скорости после закачки"].append(
                fact_speed_injection.value
            )
            break
    # Приемистость скважины на 3-й скорости
    for fact_speed_injection in facts_speed_injection:
        if fact_speed_injection.field_name[0] == "3":
            data["Приемистость скважины на 3-й скорости после закачки"].append(
                fact_speed_injection.value
            )
            break

    # Согласовано
    AGREED = morph_pipeline(["Cогласовано", "по согласованию"])
    parser_agreed = Parser(AGREED)
    matches = list(parser_agreed.findall(text_act))
    if len(matches) > 0:
        data["Согласовано"].append("Да")
    else:
        data["Согласовано"].append("Нет")

    return data


if __name__ == "__main__":
    path = "AKT_KRS_2198_АН.pdf"
    data = defaultdict(list)
    data = get_technology(data, path)
    df = pd.DataFrame(data=data)
    df.to_excel("таблица_ГЭР.xlsx")
