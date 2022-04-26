LEFT = 1
RIGHT = 2
TOP = 4
BOTTOM = 8

DELTAS = [(LEFT, 0, -1),
          (RIGHT, 0, 1),
          (TOP, -1, 0),
          (BOTTOM, 1, 0)]

LR = LEFT | RIGHT
TB = TOP | BOTTOM
TL = TOP | LEFT
TR = TOP | RIGHT
BL = BOTTOM | LEFT
BR = BOTTOM | RIGHT

DIR_TYPES = [LR, TB, TL, TR, BL, BR]

DIR_FLIP = {
    LEFT: RIGHT,
    RIGHT: LEFT,
    TOP: BOTTOM,
    BOTTOM: TOP
    }

DIR_LOOKUP = {
    LR: '─',
    TB: '│',
    TL: '┘',
    TR: '└',
    BL: '┐',
    BR: '┌'
    }

RESULT_STRINGS = dict(s='successful',
                      f='failed',
                      u='unsolvable')

ANSI_LOOKUP = dict(R=101, B=104, Y=103, G=42,
                   O=43, C=106, M=105, m=41,
                   P=45, A=100, W=107, g=102,
                   T=47, b=44, c=46, p=35)

ANSI_RESET = '\033[0m'

ANSI_CELL_FORMAT = '\033[30;{}m'
