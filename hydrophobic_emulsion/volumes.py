from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline, pipeline
from yargy import rule, and_, Parser, or_
from yargy_utils import TOKENIZER, ID_TOKENIZER, DECIMAL, PERCENT, INT


def extract_solution_volumes(text):
    tokens = list(TOKENIZER(text))
    SOLUTION = morph_pipeline(['раствор'])
    NEFTENOL = morph_pipeline(['Нефтенол'])
    WATER = morph_pipeline(['вода'])
    UNIT_VOLUME = rule(or_(DECIMAL, rule(INT)), morph_pipeline(['м3']))
    parser = Parser(or_(UNIT_VOLUME, SOLUTION, NEFTENOL, WATER), tokenizer=ID_TOKENIZER)
    matches = parser.findall(tokens)
    spans = [_.span for _ in matches]

    # print(spans)
    def is_inside_span(token, span):
        token_span = token.span
        return span.start <= token_span.start and token_span.stop <= span.stop

    def select_span_tokens(tokens, spans):
        for token in tokens:
            if any(is_inside_span(token, _) for _ in spans):
                yield token

    tokens = list(select_span_tokens(tokens, spans))
    Volumes = fact(
        'Volumes',
        ['solution_value', 'neftenol_value', 'water_value']
    )
    VOLUMES = rule(
        SOLUTION, UNIT_VOLUME.interpretation(Volumes.solution_value),
        UNIT_VOLUME.interpretation(Volumes.neftenol_value),
        NEFTENOL, UNIT_VOLUME.interpretation(Volumes.water_value), WATER).interpretation(Volumes)
    parser = Parser(VOLUMES, tokenizer=ID_TOKENIZER)
    matches = list(parser.findall(tokens))
    if matches:
        for match in matches:
            return match.fact
