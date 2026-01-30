# backend/terminals.py

TERMINAIS = {
    0: [0],
    1: [1, 11, 21, 31],
    2: [2, 12, 22, 32],
    3: [3, 13, 23, 33],
    4: [4, 14, 24, 34],
    5: [5, 15, 25, 35],
    6: [6, 16, 26, 36],
    7: [7, 17, 27],
    8: [8, 18, 28],
    9: [9, 19, 29]
}

def get_terminal(num: int):
    for terminal, nums in TERMINAIS.items():
        if num in nums:
            return terminal
    return None
