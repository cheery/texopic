from collections import namedtuple

def read_file(filename):
    with open(filename, 'r') as fd:
        source = fd.read().decode('utf-8')
    return read_string(source)

def read_string(source):
    stream = Stream(source)
    while stream.filled:
        yield next_token(stream)

# Below, the plaintext stream is transformed into sequence of characters
# and macro words. Lines consumed by ## are annotated into that token.
Token = namedtuple("Token", ["macro", "string", "pre", "nl", "col", "lno"])
def next_token(stream):
    col = stream.col
    lno = stream.lno
    sp = stream.sp
    nl = stream.nl
    ch = stream.advance()
    if ch == ";" and stream.ahead("#"):
        ch = stream.advance()
        sp = True
    if (sp or nl) and ch == "#":
        nl = False # nl in macro tells whether there were ';'
        name = "#"
        while stream.filled:
            if stream.current == ";":
                stream.advance()
                stream.sp = True
                nl = True
                break
            if stream.current in "{}\r\n":
                break
            if stream.current.isspace():
                break
            name += stream.advance()
        capture = None if name != "##" or nl else precapture(stream)
        return Token(True, name, capture, nl, col, lno)
    return Token(False, ch, None, nl, col, lno)

# The precapture runs after every #pre -macro.
# This allows the whole stream to be tokenized
# before there is awareness about how it is used.
def precapture(stream):
    while stream.filled and stream.current != "\n" and stream.current.isspace():
        stream.advance()
    if not stream.ahead("\n"):
        return None # precapture botched
    indent = stream.indent
    lines = []
    line = []
    while stream.filled:
        if not stream.ahead("\n"):
            line.append(stream.advance())
            continue
        while stream.filled and stream.current.isspace():
            if stream.current == '\n':
                lines.append("".join(line))
                line = []
                stream.advance()
            else:
                line.append(stream.advance())
        if stream.indent <= indent:
            break
    if stream.filled: # on mid-stream behavior the last line ends up empty.
        lines.pop()
    lines.pop(0) # strip first "line" after the macro. it's always empty.
    # The precaptured block is left-stripped from space and tab characters
    # in equal amount per line.
    leftpad = 0
    try:
        leftpad = min(len(line) - len(line.lstrip(" \t")) for line in lines
            if len(line.strip()) > 0)
    except ValueError as v:
        pass
    return "\n".join(line[leftpad:] for line in lines)

# This makes the token chopper simpler to implement.
class Stream(object):
    def __init__(self, source, col=0, lno=1, indent=0):
        self.source = source
        self.index = 0
        self.sp = True
        self.nl = True
        self.col = col
        self.lno = lno
        self.indent = indent

    @property
    def filled(self):
        return self.index < len(self.source)

    @property
    def current(self):
        return self.source[self.index]

    def advance(self):
        ch = self.source[self.index]
        self.index += 1
        self.sp = ch.isspace()
        if self.sp:
            self.nl |= (ch == '\n')
            self.indent += self.nl
        else:
            self.nl  = (ch == '\n')
        if ch == '\n':
            self.indent = 0
            self.col = 0
            self.lno += 1
        else:
            self.col += 1
        return ch

    def ahead(self, ch):
        if self.index < len(self.source):
            return self.source[self.index] == ch
        return False

    def chop(self):
        return next_token(self)
