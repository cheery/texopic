# This algorithm is CS-TR-79-770
# More information: https://github.com/cheery/json-algorithm

# The scanner runs three line widths before the printer and
# checks how many spaces the blanks and groups take. This
# allows the printer to determine whether the line or
# grouping should be broken into multiple lines.

class Scanner(object):
    def __init__(self, fd, margin=80):
        self.printer = Printer(fd, margin)
        self.stream = [] 
        self.stack = []
        self.lastblank = None
        self.left_total = 1
        self.right_total = 1 # The digit '1' makes sure we
                             # won't treat the first item
                             # differently than others.

    def left(self):
        return self(Left())

    def right(self):
        return self(Right())

    def blank(self, text, indent=0, forceable=True):
        return self(Blank(text, indent, forceable))

    def __call__(self, x):
        if isinstance(x, Left):
            x.size = -self.right_total
            self.stack.append(x)
        elif isinstance(x, Right):
            if len(self.stack) > 0:
                self.stack.pop().size += self.right_total
        elif isinstance(x, Blank):
            if self.lastblank is not None:
                self.lastblank.size += self.right_total
            self.lastblank = x
            x.size = -self.right_total
            self.right_total += len(x.text)
        else:
            self.right_total += len(x)
        self.stream.append(x)
        while len(self.stream) > 0 and self.right_total - self.left_total > 3*self.printer.margin:
            self.left_total += self.printer(self.stream.pop(0))
        return self

    def finish(self):
        if self.lastblank is not None:              # Without this the last blank
            self.lastblank.size += self.right_total # gets very different treatment.
        while len(self.stream) > 0:
            self.printer(self.stream.pop(0))
        self.printer.fd.write('\n')

# Printer keeps the track of layout during printing.
class Printer(object):
    def __init__(self, fd, margin):
        self.fd = fd
        self.margin = margin
        self.layout = Layout(None, margin, False)
        self.spaceleft = margin
        self.spaces = margin

    def __call__(self, x):
        if isinstance(x, Left):
            self.layout = Layout(self.layout,
                self.spaces,
                x.size < 0 or self.spaceleft < x.size)
            return 0
        elif isinstance(x, Right):
            if self.layout.parent:
                self.layout = self.layout.parent
            return 0
        elif isinstance(x, Blank):
            if (x.size < 0 or self.spaceleft < x.size or
                    self.layout.force_break and x.forceable):
                self.spaces = self.layout.spaces - x.indent
                self.spaceleft = self.spaces
                self.fd.write('\n' + ' '*(self.margin - self.spaces))
            else:
                self.fd.write(x.text.encode('utf-8'))
                self.spaceleft -= len(x.text)
            return len(x.text)
        else:
            self.fd.write(x.encode('utf-8'))
            self.spaceleft -= len(x)
            return len(x)

# These remaining small objects are scanner and printer
# internals.

# Layout object forms a context stack to keep track of the
# margin. force_break forces forceable Blanks broken.
class Layout(object):
    def __init__(self, parent, spaces, force_break):
        self.parent = parent
        self.spaces = spaces
        self.force_break = force_break

# These objects are mutated by the scanner, so they cannot
# be reused. Users of the pretty printer should not create
# them themselves. They should use the .left(), .right() and
# .blank() helpers.
class Left(object):
    def __init__(self):
        self.size = 0 # these are calculated by the scanner.

class Right(object):
    pass

class Blank(object):
    def __init__(self, text, indent, forceable):
        self.text = text
        self.indent = indent
        self.size = 0
        self.forceable = forceable
