from main import EventyrBot
from re import match

eb = EventyrBot()

TEST_DICE_TYPES = [4, 6, 8, 10, 12, 20, 100]


def test_simple_roll():
    for dice_type in [4, 6, 8, 10, 12, 20, 100]:
        for _ in range(100):
            r = eb.roll(f'1d{dice_type}')
            assert 1 <= int(r) <= dice_type, f'Rolling 1d{dice_type} returned {r}, should be integer from 1 to {dice_type}'


def test_d20_with_fixed_modifier():
    for _ in range(100):
        r = eb.roll('1d20 + 4')
        m = match('\\d{1,2} \\+ 4 = \\d{1,2}', r)
        assert m is not None, f'Roll {r} does not match expected pattern roll + modifier = result'
        d20_roll = int(r[:r.index('+')])
        result = int(r[r.index('=') + 1:])
        assert result == d20_roll + 4, f'Equation {r} is not valid'


def test_any_dice_with_positive_modifier():
    for dice_type in TEST_DICE_TYPES:
        for modifier in range(1, 11):
            for _ in range(100):
                r = eb.roll(f'1d{dice_type} + {modifier}')
                m = match(f'\\d+ \\+ {modifier} = \\d+', r)
                assert m is not None, f'Rolling 1d{dice_type} + {modifier} yielded {r}'
                dice_roll = int(r[:r.index('+')])
                result = int(r[r.index('=') + 1:])
                assert result == dice_roll + modifier, f'Equation {r} is not valid'


def test_any_dice_with_negative_modifier():
    for dice_type in TEST_DICE_TYPES:
        for modifier in range(1, 11):
            r = eb.roll(f'1d{dice_type} - {modifier}')
            m = match(f'\\d+ - {modifier} = -?\\d+', r)
            assert m is not None, f'Rolled 1d{dice_type} - {modifier}, got {r}. Expected pattern [roll - modifier = result]'
            dice_roll = int(r[:r.index('-')])
            result = int(r[r.index('=') + 1:])
            assert result == dice_roll - modifier, f'Equation {r} is not valid'
        

def test_any_dice_with_unknown_modifier():
    for modifier in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
        for dice_type in TEST_DICE_TYPES:
            for _ in range(100):
                r = eb.roll(f'1d{dice_type} + {modifier}')
                assert match(f'\\d+ \\+ {modifier}', r) is not None, f'Rolled 1d{dice_type} + {modifier}, got {r}'
                dice_roll = int(r[:r.index('+')])
                assert 1 <= dice_roll <= dice_type


def test_multiple_dice():
    for dice_type in TEST_DICE_TYPES:
        for dice_count in range(2, 11):
            for _ in range(100):
                r = eb.roll(f'{dice_count}d{dice_type}')
                assert match(f'\\d+( \\+ \\d+){"{"}{dice_count - 1}{"}"} = \\d+', r) is not None
                parts, result = r.split('=')
                result = int(result)
                assert sum(int(part) for part in parts.split('+')) == result
                assert all(1 <= int(part) <= dice_type for part in parts.split('+'))


def test_multiple_dice_with_modifier():
    for dice_type in TEST_DICE_TYPES:
        for dice_count in range(2, 11):
            for modifier in range(1, 11):
                for _ in range(100):
                    r = eb.roll(f'{dice_count}d{dice_type} + {modifier}')
                    assert match(f'\\d+( \\+ \\d+){"{"}{dice_count - 1}{"}"} \\+ {modifier} = \\d+', r) is not None, f'Rolled {dice_count}d{dice_type} + {modifier}, got {r}'
                    parts, result = r.split('=')
                    result = int(result)
                    assert sum(int(part) for part in parts.split('+')) == result
                    assert all(1 <= int(part) <= dice_type for part in parts.split('+')[:-1])

def test_combined_dice():
    for dice_type_1 in TEST_DICE_TYPES:
        for dice_type_2 in TEST_DICE_TYPES:
            for _ in range(100):
                r = eb.roll(f'1d{dice_type_1} + 1d{dice_type_2}')
                assert match('\\d+ \\+ \\d+ = \\d+', r) is not None
                parts, result = r.split('=')
                result = int(result)
                parts = parts.split('+')
                assert sum(int(part) for part in parts) == result
                assert 1 <= int(parts[0]) <= dice_type_1
                assert 1 <= int(parts[1]) <= dice_type_2

def test_combined_dice_with_modifier():
    for dice_type_1 in TEST_DICE_TYPES:
        for dice_type_2 in TEST_DICE_TYPES:
            for modifier in [2, 5]:
                for _ in range(25):
                    r = eb.roll(f'1d{dice_type_1} + 1d{dice_type_2} + {modifier}')
                    assert match(f'\\d+ \\+ \\d+ \\+ {modifier} = \\d+', r) is not None
                    parts, result = r.split('=')
                    result = int(result)
                    parts = parts.split('+')
                    assert sum(int(part) for part in parts) == result
                    assert 1 <= int(parts[0]) <= dice_type_1
                    assert 1 <= int(parts[1]) <= dice_type_2

def test_subtracting_dice():
    for positive_dice_type in TEST_DICE_TYPES:
        for negative_dice_type in TEST_DICE_TYPES:
            r = eb.roll(f'1d{positive_dice_type} - 1d{negative_dice_type}')
            assert match('\\d+ - \\d+ = -?\\d+', r) is not None
            parts, result = r.split('=')
            result = int(result)
            add, subtract = parts.split('-')
            add = int(add)
            subtract = int(subtract)
            assert add - subtract == result
            assert 1 <= add <= positive_dice_type
            assert 1 <= subtract <= negative_dice_type

def test_deterministic_rolls():
    assert eb.roll('3d1 + 3') == '1 + 1 + 1 + 3 = 6'
    assert eb.roll('2d1 + cha') == '1 + 1 + cha = 2 + cha'
    assert eb.roll('2d1 +1d1 + dewomk+  3d1 +3+2+1') == '1 + 1 + 1 + dewomk + 1 + 1 + 1 + 3 + 2 + 1 = 12 + dewomk'



if __name__ == '__main__':
    test_simple_roll()
    test_d20_with_fixed_modifier()
    test_any_dice_with_positive_modifier()
    test_any_dice_with_negative_modifier()
    test_any_dice_with_unknown_modifier()
    test_multiple_dice()
    test_multiple_dice_with_modifier()
    test_combined_dice()
    test_combined_dice_with_modifier()
    test_subtracting_dice()
    test_deterministic_rolls()
    print('All tests successful')
