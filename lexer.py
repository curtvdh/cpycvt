import re
from typing import List, Optional
from enum import Enum


# exception class
class ParserError(Exception):
    def __init__(self, message):
        self.message = message


# rule class
# rules consist of regular expression and enum
# optional flags:
#   isws = rule is whitespace (token is ignored)
#   iscomment = rule is a comment (token is ignored)
#   iseof = rule is EOF (token will be inserted to end of token list)
class Rule:
    pattern = None

    def __init__(self, enum: Enum, regex: str, group: int = 0, is_ws: bool = False,
                 is_eof: bool = False, is_comment: bool = False, flags=None):
        self.group: int = group
        self.enum: Enum = enum
        self.is_ws: bool = is_ws
        self.is_eof: bool = is_eof
        self.is_comment: bool = is_comment
        self.regex: str = regex
        self.pattern: re.Pattern = None
        self.flags = flags

    def compile(self):
        if self.regex:
            if self.flags:
                self.pattern = re.compile(self.regex, self.flags)
            else:
                self.pattern = re.compile(self.regex)


class Range:

    def __init__(self, line_number: int, start: int, end: int):
        self.line_number: int = line_number
        self.start: int = start
        self.end: int = end


# token class
# token consists of enum and matched text
class Token:
    def __init__(self, enum: Enum, text: str, line: int, col: int):
        self.enum: Enum = enum
        self.text: str = text
        self.line: int = line
        self.col: int = col

    def __str__(self) -> str:
        return "({}:{}) enum={}, text='{}'".format(self.line, self.col, self.enum, self.text)

    def __repr__(self) -> str:
        return self.__str__()


####################################################
# Simple tokenizer
# Child classes should override the setup() method
####################################################
class Lexer:
    # constructor
    # data = string to be tokenized
    def __init__(self, data: Optional[str]):
        self.data: str = data
        self.tokens: List[Token] = []
        self.rules: List[Rule] = []
        self.eof_rule: Rule = None
        self.lines: List[Range] = []

    # Create a list of start and end positions for each newline in the data
    def break_lines(self) -> List[Range]:
        lines = [Range(1, 0, 0)]
        for index, char in enumerate(self.data):
            if char == '\n':
                lines[-1].end = index
                lines.append(Range(lines[-1].line_number + 1, index + 1, 0))
        lines[-1].end = len(self.data) - 1
        return lines

    # Get line number and column for specified position
    def find_line_col(self, pos: int):
        for line in self.lines:
            if line.start <= pos <= line.end:
                return line.line_number, pos - line.start + 1
        return None

    # add rule to list
    def add_rule(self, rule: Rule):
        self.rules.append(rule)
        if rule.is_eof:
            self.eof_rule = rule

    # parse - split data into list of Tokens
    def parse(self, data=None):
        if data:
            self.data = data
            self.tokens = []
        self.lines = self.break_lines()
        # Compile all rules
        for rule in self.rules:
            rule.compile()
        curr_pos = 0    # position in string
        
        # loop until end of input data
        while curr_pos < len(self.data):
            # traverse rules, match against current string
            while True:
                # initialize list of matched patterns
                matched = []
                
                # loop through rules - add each matched rule to list
                for rule in self.rules:
                    if not rule.pattern:
                        continue
                    m = rule.pattern.match(self.data[curr_pos:])
                    if m:
                        matched.append((rule, m))
                        
                # check if any rules matched
                line, col = self.find_line_col(curr_pos)
                if len(matched) == 0:
                    message = 'String at ({}:{}) did not match any rules\nToken starts with "{}"'\
                        .format(line, col, self.data[curr_pos:curr_pos + 10])
                    if len(self.tokens) > 1:
                        self.print_token_trace(10)
                    raise ParserError(message)
                else:
                    # find longest matched token
                    ln = 0
                    index = 0
                    for i in range(len(matched)):
                        if len(matched[i][1].group(0)) > ln:
                            ln = len(matched[i][1].group(0))
                            index = i
                    rule = matched[index][0]
                    matcher = matched[index][1]
                    
                    # add token to list
                    if not (rule.is_ws or rule.is_comment):
                        token = Token(rule.enum, matcher.group(rule.group), line, col)
                        self.tokens.append(token)
                    curr_pos += len(matcher.group(0))
                    
                # append EOF token if defined
                if curr_pos >= len(self.data):
                    if self.eof_rule:
                        self.tokens.append(Token(self.eof_rule.enum, '<EOF>', line, col))
                    break

            return self.tokens

    def print_token_trace(self, num: int = 10):
        print('### Token trace (last {} tokens)'.format(num))
        start = len(self.tokens) - 1
        end = start - num
        if end < 0:
            end = 0
        for i in range(start, end, -1):
            token = self.tokens[i]
            text = token.text.replace('\n', r'\n')
            print('{}:{}: {} (length={})'.format(token.line, token.col, text[0:40], len(text)))
        print('###')

    ############################################
    # Override this method to initialize rules
    ############################################
    def setup(self):
        pass


class Parser:

    ##########
    # Constructor - sets lexer object
    ##########
    def __init__(self, lexer: Lexer):
        self.lexer: Lexer = lexer
        self.tokens: List[Token] = []           # list of Tokens returned from lexer
        self.token_ptr: int = 0                      # index into token list
        self.curr_token: Token = None
        self.next_token: Token = None

    ##########
    # get Token list and initialize first Token
    ##########
    def start(self, data=None):
        self.tokens = self.lexer.parse(data)        # Initialize list of Tokens
        self.advance_token()

    ##########
    # returns False if all tokens have been read
    ##########
    def has_next(self) -> bool:
        return self.next_token is not None

    ##########
    # move to next Token in list
    ##########
    def advance_token(self):
        self.curr_token = self.next_token
        if self.token_ptr < len(self.tokens):
            self.next_token = self.tokens[self.token_ptr]
            self.token_ptr += 1
        else:
            self.next_token = None
        return self.curr_token

    ##########
    # report a token mismatch
    ##########
    @staticmethod
    def report(expected_enum: Enum, actual_token: Token, match: str = None):
        if match:
            message = f"expected string '{match}' ({expected_enum}) "
        else:
            message = f"expected token {expected_enum} "
        message += f" at ({actual_token.line}:{actual_token.col}) but found '{actual_token.text}' ({actual_token.enum})"
        raise ParserError(message)

    ##########
    # try to match specified token and optional text
    # required flag specifies that the token is not optional
    # advance token pointer if found
    ##########
    def match_token(self, enum: Enum, match: str = None, required: bool = False):
        if self.has_next():
            if self.next_token.enum == enum and (self.next_token.text == match if match else True):
                self.advance_token()
                return True
            else:
                if required:            # raise exception if required flag is set
                    self.report(enum, self.next_token, match)
                else:
                    return False
        else:
            raise ParserError('unexpected end of input')
        return False

    ##########
    # try to match stream of tokens
    # if successful, returns a list of matched tokens
    ##########
    def match_token_stream(self, enum_list: List[Enum], required: bool = False) -> List[Token]:
        ta: List[Token] = []
        mark = self.token_ptr               # save token pointer for rollback
        _ct = self.curr_token
        _nt = self.next_token
        for enum in enum_list:
            if self.match_token(enum, required=required):
                ta.append(self.curr_token)
            else:
                self.token_ptr = mark       # rollback
                self.curr_token = _ct
                self.next_token = _nt
                return []
        return ta

