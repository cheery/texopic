import re
import tokenizer

def read_file(path):
    return parse(tokenizer.read_file(path))

def read_string(string):
    return parse(tokenizer.read_string(string))

def parse(tokens):
    stack = []
    sequence = []
    count = 0
    last_macro = None
    space = True

    for token in tokens:
        space &= token.string.isspace()
        if not token.macro:
            if token.string == '{':
                if last_macro:
                    sequence[sequence.index(last_macro)+1:] = []
                    stack.append((sequence, count))
                    sequence = []
                    count = 0
                    last_macro.groups.append(sequence)
                else:
                    count += 1
                    sequence.append(token.string)
                last_macro = None
            elif token.string == '}':
                if len(stack) > 0 and count == 0:
                    sequence, count = stack.pop()
                    last_macro = sequence[-1]
                else:
                    count -= 1
                    sequence.append(token.string)
            elif token.nl and token.string == "\n" and not space:
                if len(stack) == 0:
                    yield sequence
                    sequence = []
                    space = True
                else:
                    sequence.append(token.string)
                last_macro = None
            else:
                if not token.string.isspace():
                    last_macro = None
                sequence.append(token.string)
        elif hexmacro.match(token.string):
            number = int(token.string[1:], 16)
            sequence.append(Escape(unichr(number), 'hex'))
            last_macro = None
        elif unimacro.match(token.string):
            number = int(token.string[3:], 16)
            sequence.append(Escape(unichr(number), 'unicode'))
            last_macro = None
        elif token.string == "##" and token.pre is not None:
            sequence.append(Pre(token.pre))
            last_macro = None
            if len(stack) == 0 and count == 0:
                yield sequence
                sequence = []
                space = True
        else:
            last_macro = Macro(token.string)
            sequence.append(last_macro)
            # nl in macro tells us whether there was ';'
            # This is used to allow or prevent grouping.
            if token.nl:
                last_macro = None
    while len(stack) > 0:
        sequence, count = stack.pop()
    yield sequence

hexmacro = re.compile(r"^#[0-9a-fA-F]{2}$")
unimacro = re.compile(r"^#U\+[0-9a-fA-F]+$")

class Escape(object):
    def __init__(self, character, which='uni'):
        self.character = character
        self.which = which

    def __str__(self):
        return self.character

class Macro(object):
    def __init__(self, name):
        self.name = name
        self.groups = []

    def __str__(self):
        return ";" + self.name + ''.join(
            '{'+''.join(map(str, group))+'}'
            for group in self.groups) + ";"

class Pre(object):
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return ";##\n"
