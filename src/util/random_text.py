from random import random


def get_random_top_text():
    # Cool banner texts
    text = [
        'typeof NaN = "number"',
        '9999999999999999 = 10000000000000000',
        '0.5 + 0.1 === 0.6',
        '0.1 + 0.2 === 0.3',
        'Math.max() = -Infinity',
        'Math.min() = Infinity',
        '[] + [] = ""',
        '[] + {} = "[object Object]"',
        '{} + [] = 0',
        'true + true + true === 2',
        'true - true = 0',
        'true == 1',
        'true === 1 = false',
        '(![] + [] + ![]).length = 9',
        '9 + "1" = "91"',
        '91 - "1" = 90',
        '[] == 0 = true',
        '2 + 2 - 2 = 2',
        '"2" + "2" - "2" = 20'
    ]

    return text[round((len(text) - 1) * random())]
