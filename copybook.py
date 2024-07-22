from enum import Enum
from typing import Optional, List, Union
from picture import Picture, PictureDecoder, PictureType
import re
import argparse
import sys
import json
import yaml
from datetime import datetime


######################
# Exception classes
######################
class CopybookException(Exception):

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


######################
# Tags
######################
class Tags(Enum):
    T_LEVEL = 'level'
    T_TYPE = 'type'
    T_LENGTH = 'length'
    T_SIGNED = 'signed'
    T_SCALE = 'scale'
    T_USAGE = 'usage'
    T_VALUES = 'values'
    T_CHILDREN = 'children'
    T_OCCURS = 'occurs'
    T_REDEFINES = 'redefines'
    T_INDEXED_BY = 'indexed_by'
    T_TIMESTAMP = 'timestamp'
    T_SOURCE = 'source'
    T_RECORD = 'record'
    T_ENUM = 'enum'
    T_DEFAULT = 'default'


######################
# Node types
######################
class _NodeType(Enum):
    N_NONE = 'none'
    N_RECORD = 'record'
    N_PICTURE = 'picture'
    N_ENUM = 'enum'


######################
# Usage types
######################
class _UsageType(Enum):
    U_NONE = 'none'
    U_PACKED = 'packed'
    U_DISPLAY = 'display'
    U_BINARY = 'binary'


######################
# Token types
######################
class _TokenEnum(Enum):
    T_TEXT = 'text'
    T_PERIOD = '.'
    T_EOF = 'eof'


######################
# Node class
# Encapsulates a single copybook entry
######################
class Node:

    def __init__(self, name: str, level: int, node_type: _NodeType, picture: Optional[Picture] = None,
                 redefines: str = None, occurs: int = 1, usage=_UsageType.U_NONE, enum_set: List = None,
                 indexed_by: str = None):
        self.node_name = name               # Element name from copybook
        self.node_type = node_type          # Node type (record, string, numeric etc.)
        self.node_level = level             # Node level
        self.redefines = redefines          # Redefines flag
        self.occurs = occurs                # Number of occurrences
        self.node_picture = picture         # Node picture (Picture object from picture.py)
        self.usage = usage                  # Node usage (packed, display, binary etc.)
        self.enum_set = enum_set            # Enums (level 88)
        self.indexed_by = indexed_by        # Indicates variable name for indexing

    def __str__(self):
        s = f'Node: level={self.node_level}, name={self.node_name}, type={self.node_type}'
        if self.node_picture:
            s += f', picture={self.node_picture}'
        if self.usage != _UsageType.U_NONE:
            s += f', usage={self.usage}'
        if self.enum_set:
            s += f', enum_value={self.enum_set}'
        return s

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        """
        Converts node to dictionary
        :return: dict
        """
        output = {'level': self.node_level}

        # RECORD type
        if self.node_type == _NodeType.N_RECORD:
            output.update({'type': 'record'})
        # PICTURE type
        elif self.node_type == _NodeType.N_PICTURE:
            output.update({'length': self.node_picture.length})
            if self.node_picture.default:
                output.update({'length': self.node_picture.default})
            # STRING type
            if self.node_picture.picture_type == PictureType.P_STRING:
                output.update({'type': 'string'})
            # NUMERIC type
            elif self.node_picture.picture_type == PictureType.P_NUMERIC:
                output.update({'type': 'numeric'})
                output.update({'signed': self.node_picture.signed})
                if self.node_picture.scale:
                    output.update({'scale': self.node_picture.scale})
            if self.usage != _UsageType.U_NONE:
                output.update({'usage': self.usage.value})
        elif self.node_type == _NodeType.N_ENUM:
            output.update({'type': 'enum'})
            output.update({'values': ','.join(self.enum_set)})
        if self.occurs > 1:
            output.update({'occurs': self.occurs})
        if self.redefines:
            output.update({'redefines': self.redefines})
        if self.indexed_by:
            output.update({'indexed_by': self.indexed_by})
        return output


######################
# Factory function
# Generates Node objects from dictionary
######################
def make_node(element: dict) -> Node:
    """
    Creates a Node object from the supplied dictionary
    :param element:
    :return: Node object
    """

    def get_value(key: str, container: dict) -> Union[str, int, bool]:
        """
        Wrapper for dictionary key get
        :param key:
        :param container:
        :return:
        """

        try:
            return container[key]
        except KeyError:
            raise CopybookException(f"Could not find key '{key}' in:\n{container}")

    def make_picture(container: dict) -> Picture:
        """
        Creates a Picture object from dictionary
        :param container:
        :return: Picture object
        """

        picture = Picture()
        try:
            picture.picture_type = PictureType(get_value(Tags.T_TYPE.value, container)).name
        except ValueError:
            raise CopybookException(f"Unknown value for 'type' field: {get_value(Tags.T_TYPE.value, container)}")
        if Tags.T_LENGTH.value in container:
            picture.length = get_value(Tags.T_LENGTH.value, container)
        if Tags.T_SCALE.value in container:
            picture.scale = get_value(Tags.T_SCALE.value, container)
        if Tags.T_SIGNED.value in container:
            picture.signed = get_value(Tags.T_SIGNED.value, container)
        if Tags.T_DEFAULT.value in container:
            picture.default = get_value(Tags.T_DEFAULT.value, container)
        return picture

    name = list(element.keys())[0]
    spec = element[name]
    level = get_value(Tags.T_LEVEL.value, spec)
    if get_value(Tags.T_TYPE.value, spec) == Tags.T_RECORD.value:
        node_type = _NodeType.N_RECORD
    elif get_value(Tags.T_TYPE.value, spec) == Tags.T_ENUM.value:
        node_type = _NodeType.N_ENUM
    else:
        node_type = _NodeType.N_PICTURE

    node = Node(name, level, node_type)
    if node_type == _NodeType.N_PICTURE:
        node.node_picture = make_picture(spec)
    if Tags.T_OCCURS.value in spec:
        node.occurs = get_value(Tags.T_OCCURS.value, spec)
    if Tags.T_REDEFINES.value in spec:
        node.redefines = get_value(Tags.T_REDEFINES.value, spec)
    if Tags.T_INDEXED_BY.value in spec:
        node.indexed_by = get_value(Tags.T_INDEXED_BY.value, spec)
    if Tags.T_VALUES.value in spec:
        node.enum_set = get_value(Tags.T_VALUES.value, spec)
    return node


######################
# TreeNode class
# Wraps a Node object with parent and child references
######################
class TreeNode:

    def __init__(self, node: Node, parent):
        """
        :param node: Node object to wrap
        :param parent: Treenode object reference to parent node
        """
        self.node = node
        self.parent: TreeNode = parent
        self.children: List[TreeNode] = []

    def append(self, node):
        """
        Appends a TreeNode object to this nodes list of children
        :param node:
        :return:
        """
        self.children.append(node)

    def __str__(self):
        return f"TreeNode: {self.node.node_name} ({self.node.node_level})"

    def __repr__(self):
        return self.__str__()


######################
# Token class
# Used by tokenizer
######################
class Token:

    def __init__(self, enum: _TokenEnum, text: str, line: int, col: int):
        self.enum = enum
        self.text = text
        self.up_text = text.upper()
        self.line = line
        self.col = col

    def __str__(self):
        return f'Token: {self.enum} ({self.text})'

    def __repr__(self):
        return self.__str__()


def tokenize(text: str) -> List[Token]:
    """
    Converts copybook into a stream of Token objects
    :param text: copybook as string
    :return: List[Token]
    """

    # enums for state machine
    class State(Enum):
        S_START = 'start'
        S_TEXT = 'text'
        S_WS = 'ws'
        S_PERIOD = 'period'

    line = col = 1
    state = State.S_START
    tokens = []
    s_token = ''

    # Iterate over characters in text and convert to stream of Tokens
    for c in text:
        # S_START state
        if state == State.S_START:
            if c in [' ', '\t', '\n']:      # Look for whitespace
                if c == '\n':               # Increment line if character is a newline
                    line += 1
                    col = 0
                state = State.S_WS
            elif c == '.':                  # Look for period indicating end of copybook element definition
                if s_token:
                    tokens.append(Token(_TokenEnum.T_TEXT, s_token, line, col))
                    s_token = ''
                tokens.append(Token(_TokenEnum.T_PERIOD, '.', line, col))
                state = State.S_START
            else:
                s_token += c
        # S_WS state (whitespace)
        elif state == State.S_WS:
            if s_token:
                # Create new Token object and append to list
                tokens.append(Token(_TokenEnum.T_TEXT, s_token, line, col))
                s_token = ''
            if c in [' ', '\t', '\n']:      # Look for more whitespace
                state = State.S_WS
                if c == '\n':
                    line += 1
            elif c == '.':                  # Look for period
                tokens.append(Token(_TokenEnum.T_PERIOD, '.', line, col))
            else:
                s_token = c
                state = State.S_START
        # S_PERIOD state
        elif state == State.S_PERIOD:
            if s_token:
                # Create new Token object and append to list
                tokens.append(Token(_TokenEnum.T_TEXT, s_token, line, col))
                s_token = ''
            tokens.append(Token(_TokenEnum.T_PERIOD, '.', line, col))
            state = State.S_START
        else:
            raise CopybookException(f'Unhandled state: {state}')
        col += 1

    # append last token
    if s_token:
        tokens.append(Token(_TokenEnum.T_TEXT, s_token, line, col))
    # append EOF token
    tokens.append(Token(_TokenEnum.T_EOF, '(eof)', line, col))
    return tokens


def parse_copybook(copybook: str) -> List[Node]:
    """
    Parses copybook into list of Node objects
    :param copybook: Copybook as string
    :return: List[Node]
    """

    # Regular expressions
    re_int = re.compile(r'\d+')
    re_identifier = re.compile(r'[A-Za-z\d_\-]+')
    re_string = re.compile(r"\'([^']+)\'")

    # enums for state machine
    class State(Enum):
        S_START = 'start'
        S_SENTENCE = 'sentence'
        S_CLAUSE = 'clause'
        S_REDEFINES = 'redefines'
        S_OCCURS = 'occurs'
        S_PICTURE = 'picture'
        S_VALUE = 'value'
        S_USAGE = 'usage'
        S_ENUM = 'enum'
        S_INDEXED = 'indexed'

    def consume() -> None:
        """
        Parses copybook using state machine
        :return: None
        """
        state = State.S_START
        level = 0
        node = None
        token_idx = 0
        decoder = PictureDecoder()

        # iterate over token list obtained from tokenizer
        while token_idx < len(tokens):
            token = tokens[token_idx]

            # S_START state
            if state == State.S_START:
                if token.up_text == 'EJECT':        # Ignore EJECT
                    state = State.S_START
                elif token.enum == _TokenEnum.T_TEXT and re_int.match(token.text): # Look for level number
                    level = int(token.text)
                    state = State.S_SENTENCE
                elif token.enum == _TokenEnum.T_EOF:
                    return
                else:
                    raise CopybookException(f'Expected level number, found {token.text} at ({token.line}:{token.col})')
            # S_SENTENCE state
            elif state == State.S_SENTENCE:
                if token.enum == _TokenEnum.T_TEXT and re_identifier.match(token.text): # Look for identifier
                    node = Node(token.text, level, _NodeType.N_NONE)
                    state = State.S_CLAUSE
                else:
                    raise CopybookException(f'Expected identifier, found {token.text} at ({token.line}:{token.col})')
            # S_CLAUSE state
            elif state == State.S_CLAUSE:
                if token.enum == _TokenEnum.T_PERIOD:
                    if node.node_picture:
                        node_type = _NodeType.N_PICTURE
                    elif node.enum_set:
                        node_type = _NodeType.N_ENUM
                    else:
                        node_type = _NodeType.N_RECORD
                    node.node_type = node_type
                    node_list.append(node)
                    state = State.S_START
                elif token.up_text == 'REDEFINES':
                    state = State.S_REDEFINES
                elif token.up_text == 'OCCURS':
                    state = State.S_OCCURS
                elif token.up_text in ['PIC', 'PICTURE']:
                    state = State.S_PICTURE
                elif token.up_text == 'VALUE':
                    state = State.S_VALUE
                elif token.up_text == 'USAGE':
                    state = State.S_USAGE
                elif token.up_text in ['DISPLAY', 'BINARY', 'COMP-3', 'COMPUTATIONAL-3']:
                    usage = decode_usage(token.up_text)
                    if not usage:
                        raise CopybookException(f'Unexpected USAGE type at ({token.line}:{token.col})')
                    node.usage = usage
                    state = State.S_CLAUSE
                elif token.text == 'INDEXED':
                    state = State.S_INDEXED
                else:
                    raise CopybookException(f'Expected clause, found {token.text} at ({token.line}:{token.col})')
            # S_REDEFINES state
            elif state == State.S_REDEFINES:
                if token.enum == _TokenEnum.T_TEXT:
                    node.redefines = token.text
                    state = State.S_CLAUSE
                else:
                    raise CopybookException(f'Expected identifier, found {token.text} at ({token.line}:{token.col})')
            # S_OCCURS state
            elif state == State.S_OCCURS:
                if token.enum == _TokenEnum.T_TEXT and re_int.match(token.text):
                    node.occurs = int(token.text)
                    if tokens[token_idx + 1].up_text == 'TIMES':
                        token_idx += 1
                    state = State.S_CLAUSE
                else:
                    raise CopybookException(f'Expected occurs count, found {token.text} at ({token.line}:{token.col})')
            # S_PICTURE state
            elif state == State.S_PICTURE:
                picture = decoder.decode(token.up_text)
                if not picture:
                    raise CopybookException(f'Expected PICTURE definition, found {token.text} at ({token.line}:{token.col})')
                node.node_picture = picture
                state = State.S_CLAUSE
            # S_VALUE state
            elif state == State.S_VALUE:
                if match := re_string.match(token.text):
                    value_text = match.group(0)
                else:
                    value_text = token.text
                if node.node_picture:
                    node.node_picture.default = value_text
                else:
                    # no PICTURE clause, check for enum level
                    if level == 88:
                        node.enum_set = [value_text]
                        # peek next token
                        # if period, go to S_CLAUSE
                        # else go to S_ENUM
                        if tokens[token_idx+1].enum == _TokenEnum.T_PERIOD:
                            state = State.S_CLAUSE
                        else:
                            state = State.S_ENUM
                    else:
                        raise CopybookException(f'VALUE without PICTURE at ({token.line}:{token.col})')
            # S_USAGE state
            elif state == State.S_USAGE:
                if token.up_text == 'IS':
                    state = State.S_USAGE
                else:
                    usage = decode_usage(token.up_text)
                    if not usage:
                        raise CopybookException(f'Unexpected USAGE type at ({token.line}:{token.col})')
                    node.usage = usage
                    state = State.S_CLAUSE
            # S_ENUM state
            elif state == State.S_ENUM:
                # enums can be repeated, separated by spaces
                if match := re_string.match(token.text):
                    value_text = match.group(0)
                else:
                    value_text = token.text
                node.enum_set.append(value_text)
                if tokens[token_idx+1].enum == _TokenEnum.T_PERIOD:
                    state = State.S_CLAUSE
                else:
                    state = State.S_ENUM
            # S_INDEXED state
            elif state == State.S_INDEXED:
                if token.text == 'BY':
                    state = State.S_INDEXED
                elif token.enum == _TokenEnum.T_TEXT:
                    node.indexed_by = token.text
                    state = State.S_CLAUSE
                else:
                    raise CopybookException(f'Invalid specification for INDEXED BY at ({token.line}:{token.col})')
            token_idx += 1

    def decode_usage(u: str) -> Optional[_UsageType]:
        if u == 'DISPLAY':
            return _UsageType.U_DISPLAY
        elif u == 'BINARY':
            return _UsageType.U_BINARY
        elif u in ['COMP-3', 'COMPUTATIONAL-3']:
            return _UsageType.U_PACKED
        else:
            return None

    tokens = tokenize(copybook)
    node_list = []
    consume()
    return node_list


def build_node_tree(node_list: List[Node]) -> TreeNode:
    """
    Converts list of nodes into a hierarchical structure based on level numbers
    :param node_list: List of Node objects
    :return: TreeNode object
    """

    root = TreeNode(Node('Root', 0, _NodeType.N_RECORD), None)  # create dummy root node
    ptr = root

    # iterate over nodes
    for node in node_list:
        if node.node_level > ptr.node.node_level:
            # this node is a child of ptr
            # append node to current ptr and move ptr to new node
            new_node = TreeNode(node, ptr)
            ptr.append(new_node)
            ptr = new_node
        elif node.node_level == ptr.node.node_level:
            # this node is at the same level as ptr
            # append node to parent of ptr and move ptr to new node
            new_node = TreeNode(node, ptr.parent)
            ptr.parent.append(new_node)
            ptr = new_node
        else:
            # this node has a level number lower than ptr
            # search up the chain of nodes for the matching level number
            # append node to parent of matched search result and move ptr to new node
            search = ptr.parent
            while search.node.node_level != 0 and search.node.node_level != node.node_level:
                search = search.parent
            if search.node.node_level == 0:
                raise CopybookException(f'Could not find parent: {node}, ptr: {ptr.node}')
            new_node = TreeNode(node, search.parent)
            search.parent.append(new_node)
            ptr = new_node

    return root


def to_dict(root: TreeNode) -> dict:
    """
    Converts hierarchical structure to nested dictionary
    :param root:
    :return:
    """

    def add_children(ptr: TreeNode, output: dict):
        """
        Recursively adds children to supplied TreeNode
        :param ptr:
        :param output:
        :return:
        """
        children = []
        tree_node = None
        for tree_node in ptr.children:
            child = {}
            add_children(tree_node, child)      # Recursive call
            children.append(child)

        output[ptr.node.node_name] = {}         # Create empty dict for this TreeNode

        # RECORD type
        if ptr.node.node_type == _NodeType.N_RECORD:
            output[ptr.node.node_name].update({'type': 'record'})
        # PICTURE type
        elif ptr.node.node_type == _NodeType.N_PICTURE:
            output[ptr.node.node_name].update({'length': ptr.node.node_picture.length})
            if ptr.node.node_picture.default:
                output[ptr.node.node_name].update({'length': ptr.node.node_picture.default})
            # STRING type
            if ptr.node.node_picture.picture_type == PictureType.P_STRING:
                output[ptr.node.node_name].update({'type': 'string'})
            # NUMERIC type
            elif ptr.node.node_picture.picture_type == PictureType.P_NUMERIC:
                output[ptr.node.node_name].update({'type': 'numeric'})
                output[ptr.node.node_name].update({'signed': ptr.node.node_picture.signed})
                if ptr.node.node_picture.scale:
                    output[ptr.node.node_name].update({'scale': ptr.node.node_picture.scale})
            if ptr.node.usage != _UsageType.U_NONE:
                output[ptr.node.node_name].update({'usage': ptr.node.usage.value})
        elif ptr.node.node_type == _NodeType.N_ENUM:
            output[ptr.node.node_name].update({'type': 'enum'})
            output[ptr.node.node_name].update({'values': ','.join(ptr.node.enum_set)})
        if children:
            if tree_node:
                ls = f'{tree_node.node.node_level:02}'
                output[ptr.node.node_name].update({ls: children})
        if ptr.node.occurs > 1:
            output[ptr.node.node_name].update({'occurs': ptr.node.occurs})
        if ptr.node.redefines:
            output[ptr.node.node_name].update({'redefines': ptr.node.redefines})
        if ptr.node.indexed_by:
            output[ptr.node.node_name].update({'indexed_by': ptr.node.indexed_by})

    result = {}
    add_children(root, result)
    result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # if filename:
    #     result['source'] = filename
    return result


def load_file(filename: str) -> str:
    """
    Loads copybook with existence check
    :param filename:
    :return: contents of file
    """

    s = ''
    try:
        with open(filename, 'r') as reader:
            for line in reader.readlines():
                # look for comment lines
                if line[6] == '*':
                    s += '\n'
                else:
                    # blank columns 1 to 7 and 74 to EOL
                    s += '       ' + line[7:72].rstrip() + '\n'
        return s
    except OSError as e:
        raise CopybookException(f'Error opening {filename}: {e}')


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='name of input file', type=str)
    parser.add_argument('-output', help='output to specified filename', type=str, required=False)
    parser.add_argument('-yaml', help='output type as YAML (default is JSON)', required=False, action='store_true')
    parser.add_argument('-nested', help='output converted copybook as nested objects (default is flat)', required=False,
                        action='store_true')
    return parser.parse_args()


def main() -> int:
    args = get_args()
    if not args:
        return 1
    try:
        text = load_file(args.filename)
    except OSError as e:
        print(f'Error opening {args.filename}: {e}')
        return 1

    try:
        # Convert copybook to list of Node objects
        node_list = parse_copybook(text)

        if args.nested:
            # Build Node tree from Node list
            node_tree = build_node_tree(node_list)
            # Convert Node tree to dictionary
            node_dict = to_dict(node_tree)
        else:
            node_dict = {'nodes': [{node.node_name: node.to_dict()} for node in node_list]}

        node_dict.update({'source': args.filename})

        if args.yaml:
            # convert to YAML
            node_output = yaml.dump(node_dict, sort_keys=False)
        else:
            # Create JSON object from dictionary
            node_output = json.dumps(node_dict, indent=2)

        if args.output:
            with open(args.output, 'w') as writer:
                writer.write(node_output)
        else:
            print(node_output)

        return 0
    except CopybookException as e:
        print(f'Parse Exception: {e}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
