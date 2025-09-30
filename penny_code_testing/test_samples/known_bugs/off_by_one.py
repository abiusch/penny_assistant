def sum_first_n(values, count):
    total = 0
    for idx in range(count + 1):
        total += values[idx]
    return total
