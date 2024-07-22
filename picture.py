import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List
from lexer import Rule, Lexer, ParserError


######################
# Picture types
######################
class PictureType(Enum):
    P_NONE = 'none'
    P_STRING = 'string'
    P_NUMERIC = 'numeric'


######################
# Picture class
######################
class Picture:

    def __init__(self):
        self.picture_type: PictureType = PictureType.P_NONE
        self.length = 0
        self.scale = 0
        self.default: str = ''
        self.signed: bool = False

    def __str__(self):
        s = f'Picture: type={self.picture_type}, length={self.length}, signed={self.signed}'
        if self.scale:
            s += f', scale={self.scale}'
        if self.default:
            s += f', default={self.default}'
        return s

    def __repr__(self):
        return self.__str__()


class PictureDecoder:

    class _TokenTypes(Enum):
        T_X = 'X'
        T_9 = '9'
        T_V = 'V'
        T_S = 'S'
        T_LEN = 'len'
        T_EOL = 'eol'

    class _State(Enum):
        T_BEGIN = 'begin'
        T_SINGLE_X = 'single_x'
        T_MULTI_X = 'multi_x'
        T_SINGLE_9 = 'single_9'
        T_MULTI_9 = 'multi_9'
        T_WAIT_EOL = 'wait_eol'
        T_WAIT_FIXED_POINT = 'wait_fixed_point'

    def __init__(self):
        self.lexer: Lexer = self._setup_lexer()

    def _setup_lexer(self) -> Lexer:
        lexer = Lexer(data=None)
        lexer.add_rule(Rule(self._TokenTypes.T_X, r'X+', flags=re.IGNORECASE))
        lexer.add_rule(Rule(self._TokenTypes.T_9, r'9+'))
        lexer.add_rule(Rule(self._TokenTypes.T_V, r'V'))
        lexer.add_rule(Rule(self._TokenTypes.T_S, r'S'))
        lexer.add_rule(Rule(self._TokenTypes.T_LEN, r'\((\d+)\)', group=1))
        lexer.add_rule((Rule(self._TokenTypes.T_EOL, '', is_eof=True)))
        return lexer

    def decode(self, pic: str) -> Optional[Picture]:

        state = self._State.T_BEGIN
        picture = Picture()
        picture.signed = False
        picture.length = 0
        tokens = self.lexer.parse(pic)
        token_idx = 0

        while token_idx < len(tokens):
            token = tokens[token_idx]

            if state == self._State.T_BEGIN:
                if token.enum == self._TokenTypes.T_X:
                    if picture.picture_type != PictureType.P_NONE:
                        return None
                    picture.picture_type = PictureType.P_STRING
                    if len(token.text) == 1:
                        state = self._State.T_SINGLE_X
                    else:
                        picture.length = len(token.text)
                        state = self._State.T_WAIT_EOL
                elif token.enum == self._TokenTypes.T_9:
                    picture.picture_type = PictureType.P_NUMERIC
                    if len(token.text) == 1:
                        state = self._State.T_SINGLE_9
                    else:
                        picture.length = len(token.text)
                        state = self._State.T_WAIT_FIXED_POINT
                elif token.enum == self._TokenTypes.T_S:
                    picture.signed = True
                    picture.picture_type = PictureType.P_NUMERIC
                    state = self._State.T_BEGIN
                elif token.enum == self._TokenTypes.T_V:
                    picture.length = 0
                    picture.picture_type = PictureType.P_NUMERIC
                    state = self._State.T_WAIT_FIXED_POINT
                else:
                    return None
            elif state == self._State.T_SINGLE_X:
                if token.enum == self._TokenTypes.T_LEN:
                    picture.length = int(token.text)
                    state = self._State.T_WAIT_EOL
                elif token.enum == self._TokenTypes.T_EOL:
                    picture.length = 1
                else:
                    return None
            elif state == self._State.T_SINGLE_9:
                if token.enum == self._TokenTypes.T_LEN:
                    picture.length = int(token.text)
                    state = self._State.T_WAIT_FIXED_POINT
                elif token.enum == self._TokenTypes.T_EOL:
                    picture.length = 1
                elif token.enum == self._TokenTypes.T_V:
                    state = self._State.T_WAIT_FIXED_POINT
                else:
                    return None
            elif state == self._State.T_WAIT_FIXED_POINT:
                if token.enum == self._TokenTypes.T_V:
                    state = self._State.T_WAIT_FIXED_POINT
                elif token.enum == self._TokenTypes.T_9:
                    if len(token.text) == 1 and tokens[token_idx+1].enum == self._TokenTypes.T_LEN:
                        picture.scale = int(tokens[token_idx+1].text)
                        picture.length += picture.scale
                        token_idx += 1
                        state = self._State.T_WAIT_EOL
                    else:
                        picture.scale = len(token.text)
                        picture.length += len(token.text)
                        state = self._State.T_WAIT_EOL
                elif token.enum != self._TokenTypes.T_EOL:
                    return None
            elif state == self._State.T_WAIT_EOL:
                if token.enum != self._TokenTypes.T_EOL:
                    return None

            token_idx += 1

        return picture


if __name__ == '__main__':

    picture_decoder = PictureDecoder()
    print(picture_decoder.decode('V9(02)'))
