from collections import namedtuple
import re
import sys

class Vertical(object):
    def __init__(self):
        self.title = u""
        self.lines = []
        self.h2_count = 0

    def nonmacro(self, token):
        return self.horiz().nonmacro(token)

    def horiz(self):
        return Horizontal(self)
    
class Horizontal(object):
    def __init__(self, vertical):
        self.vertical = vertical
        self.tag = "p"
        self.line = []
        self.sp = False

    def done(self):
        if len(self.line) > 0:
            tag = None
            if self.tag == "h1":
                self.vertical.title = u"".join(self.line)
            if self.tag == "h2":
                self.vertical.h2_count += 1
                tag = str(self.vertical.h2_count)
                self.line.insert(0, "{0}. ".format(self.vertical.h2_count))
                self.line.append(' <a class="ref" href="#{0}">$</a>'.format(tag))
            if tag:
                line = u'<{0} id="{1}">{2}</{0}>'.format(
                    self.tag, tag, u"".join(self.line))
            else:
                line = u"<{0}>{1}</{0}>".format(self.tag, u"".join(self.line))
            self.vertical.lines.append(line)
            return Horizontal(self.vertical)
        return self

    def nonspace(self, string):
        if self.sp and len(self.line) > 0:
            self.line.append(u" ")
        self.sp = False
        self.line.append(string)
        return self

    def nonmacro(state, token):
        if token.nl and token.string == u"\n":
            state = state.done()
        if token.string.isspace():
            state.sp = True
        else:
            return state.nonspace(token.string)
        return state

    def horiz(self):
        return self

class ArgumentBuilder(object):
    def __init__(self, horizontal, argc, function):
        self.horizontal = horizontal
        self.argc = argc
        self.args = []
        self.arg = []
        self.brace = 0
        self.function = function

    def done(self):
        assert False # todo: put nice error message

    def nonmacro(state, token):
        if token.string.isspace():
            if len(state.arg) == 0:
                return state
            elif state.brace > 0:
                state.arg.append(token.string)
            else:
                return state.argpush()
        if token.string == u"{":
            if state.brace > 0:
                state.arg.append(token.string)
            state.brace += 1
            return state
        if token.string == u"}":
            state.brace -= 1
            if state.brace > 0:
                state.arg.append(token.string)
            else:
                return state.argpush()
            return state
        state.arg.append(token.string)
        return state

    def argpush(self):
        self.args.append(u"".join(self.arg))
        if len(self.args) < self.argc:
            self.arg = []
            self.brace = 0
            return self
        else:
            res = self.function(*self.args)
            self.horizontal.nonspace(res)
            return self.horizontal

    def horiz(self):
        return self



def macro_title(state, token, stream):
    state = state.horiz()
    state.tag = "h1"
    return state

def macro_section(state, token, stream):
    state = state.horiz()
    state.tag = "h2"
    return state

def macro_subsection(state, token, stream):
    state = state.horiz()
    state.tag = "h3"
    return state

def macro_pre(state, token, stream):
    state = state.done()
    if token.pre:
        pre = u"<pre>{}</pre>".format(token.pre)
        state.vertical.lines.append(pre)
    return state

def macro_url(state, token, stream):
    make_url = u'<a href="{0}">{0}</a>'.format
    return ArgumentBuilder(state, 1, make_url)

def macro_href(state, token, stream):
    make_url = u'<a href="{0}">{1}</a>'.format
    return ArgumentBuilder(state, 2, make_url)

macros = {
    "#title": macro_title,
    "#pre": macro_pre,
    "#url": macro_url,
    "#href": macro_href,
    "#section": macro_section,
    "#subsection": macro_subsection,
}

html_template = u"""<html>
<head>
<meta charset="utf-8">
<title>{0}</title>
<style>
body {{ max-width: 75ex }}
pre {{ border: 1px solid #cfcfcf; padding: 1em 4ex }}
h2        > .ref {{ visibility: hidden; text-decoration: none; }}
h2:hover > .ref {{ visibility: visible !important }}
</style>
</head>
<body>
{1}
</body>
</html>"""

hexmacro = r"^#[0-9a-fA-F]{2}$"
unimacro = r"^#U\+[0-9a-fA-F]+$"

def main():
    with open(sys.argv[1], 'r') as fd:
        source = fd.read().decode('utf-8')
    stream = Stream(source)

    state = root = Vertical()
    while stream.filled:
        token = next_token(stream)
        if not token.macro:
            state = state.nonmacro(token)
        elif token.string in macros:
            state = macros[token.string](state, token, stream)
        elif re.match(hexmacro, token.string):
            number = (int(token.string[1:], 16))
            state = state.nonspace(unichr(number))
        elif re.match(unimacro, token.string):
            number = (int(token.string[3:], 16))
            state = state.nonspace(unichr(number))
        else:
            state = state.nonmacro(token)
    state.done()
    out = html_template.format(root.title, u"\n".join(root.lines))
    print out.encode('utf-8')

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
        name = "#"
        while stream.filled:
            if stream.current == ";":
                stream.advance()
                stream.sp = True
                break
            if stream.current in "{}\r\n":
                break
            if stream.current.isspace():
                break
            name += stream.advance()
        capture = None if name != "#pre" else precapture(stream)
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
        lines.append("".join(line))
        line = []
        while stream.filled and stream.current.isspace():
            line.append(stream.advance())
        if stream.indent <= indent:
            break
    lines.pop(0) # strip first "line" after the macro. it's always empty.
    # The precaptured block is left-stripped from space and tab characters
    # in equal amount per line.
    leftpad = 0
    if len(lines) > 0:
        leftpad = min(len(line) - len(line.lstrip(" \t\n")) for line in lines)
    return "\n".join(line[leftpad:] for line in lines)

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

if __name__=="__main__":
    main()
