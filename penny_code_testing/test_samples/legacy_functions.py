def legacy_calculation(a, b, c):
    result = 0
    for value in (a, b, c):
        if value:
            result += value * 2
        else:
            result += 1
    return result
