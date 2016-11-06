from structures import Escape, Macro, Pre
# Generic functionality to create a texopic processor.
#
# Will likely change a bit over time.
# There is example of use in texopic2html.py -script.

class Env(object):
    def __init__(self):
        self.env = {}

    def define(self, name, arity):
        def _deco_(fn):
            self.env[(name, arity)] = fn
            return fn
        return _deco_

    def __call__(self, ctx, name, groups):
        key = (name, len(groups))
        if key in self.env:
            return self.env[key](ctx, *groups)
        return None

def invoke(group, document, **kwargs):
    context = Context(document, **kwargs)
    context = process(context, group)
    while context.parent is not None:
        context = context.end()
    return context

class Context(object):
    def __init__(self, document, preformat, paragraph,
            do_macro, do_begin,
            block=None, name=None, parent=None):
        self.builder = Builder(paragraph)
        self.document = document
        self.preformat = preformat
        self.paragraph = paragraph
        self.do_macro = do_macro
        self.do_begin = do_begin
        self.parent = parent
        self.block = block
        self.name = name

    # I was wondering if begin/end -functions should be here.
    # But then I stopped worrying.
    def begin(self, block, name=None):
        return Context(self.document,
            self.preformat, self.paragraph,
            self.do_macro, self.do_begin,
            block, name, self)

    def end(self):
        self.parent.builder.vertical.append(self.block.end(self))
        return self.parent

    def inside(self, name):
        if name == self.name:
            return True
        elif self.parent is not None:
            return self.parent.inside(name)

    @property
    def is_horizontal(self):
        return len(self.builder.vertical) == 0

    def pull_horizontal(self):
        assert len(self.builder.vertical) == 0
        group = self.builder.group
        self.builder = Builder(self.paragraph)
        return group

    def pull_vertical(self):
        vertical = self.builder.vertical
        self.builder.next_group(self.paragraph)
        self.builder = Builder(self.paragraph)
        return vertical

    def invoke(self, group):
        context = Context(self.document, self.preformat, self.paragraph,
            self.do_macro, self.do_begin)
        context = process(context, group)
        while context.parent is not None:
            context = context.end()
        return context

def process(ctx, group):
    for node in group:
        if isinstance(node, Escape):
            ctx.builder.append(node.character)
        elif isinstance(node, (str, unicode)):
            ctx.builder.append(node, node.isspace())
        elif isinstance(node, Macro) and node.name == '':
            ctx.builder.next_group_implicit = ctx.paragraph
        elif isinstance(node, Pre):
            if ctx.builder.pre_capture:
                ctx.builder.args = [node.string] + list(ctx.builder.args)
                ctx.builder.next_group(ctx.paragraph)
            else:
                ctx.builder.next_group(ctx.paragraph)
                ctx.builder.vertical.append(ctx.preformat(node.string))
        elif isinstance(node, Macro):
            recover = True
            if node.name == "#begin" and len(node.groups) >= 1:
                name = verbatim(node.groups[0])
                new_ctx = ctx.do_begin(ctx, name, node.groups[1:])
                if new_ctx is not None:
                    recover = False
                    ctx.builder.next_group(ctx.paragraph)
                    ctx = new_ctx
                    ctx.name = name
            elif node.name == "#end":
                if len(node.groups) == 0 and ctx.parent is not None:
                    recover = False
                    ctx = ctx.end()
                    ctx.builder.next_group(ctx.paragraph)
                else:
                    name = verbatim(node.groups[0])
                    if len(node.groups) == 1 and ctx.inside(name):
                        recover = False
                        while ctx.inside(name):
                            ctx = ctx.end()
            else:
                x = ctx.do_macro(ctx, node.name, node.groups)
                if x is not None:
                    recover = False
                    if x != "":
                        ctx.builder.append(x)
            if recover:
                ctx.builder.append(node.name)
                for group in node.groups:
                    ctx.builder.append('{')
                    ctx = process(ctx, group)
                    ctx.builder.append('}')
        else:
            assert False, repr(node)
    return ctx

# There was quite big egg/chicken-contest between the Builder
# and the Context.
class Builder(object):
    def __init__(self, fn, *args):
        self.vertical = []

        self.group = []
        self.space = False
        self.fn = fn
        self.args = args
        self.pre_capture = False
        self.next_group_implicit = None

    def next_group(self, fn, *args):
        if len(self.group) > 0:
            self.vertical.append(self.fn(self.group, *self.args))
            self.group = []
        self.fn = fn
        self.args = args
        self.next_group_implicit = None
        self.pre_capture = False

    def append(self, value, is_space=False):
        if is_space:
            self.space = True
        else:
            if self.space and len(self.group) > 0:
                self.group.append(' ')
            self.space = False
            if self.next_group_implicit is not None:
                self.next_group(self.next_group_implicit)
            self.group.append(value)

# Some groups, such as contents of #begin need to be
# interpreted as plain text.
def verbatim(group):
    data = []
    for node in group:
        if isinstance(node, Escape):
            data.append(node.character)
        elif isinstance(node, Macro):
            data.append(node.name)
            for subgroup in node.groups:
                data.append(u"{")
                data.append(verbatim(subgroup))
                data.append(u"}")
            return u''.join(data)
        elif isinstance(node, Pre):
            data.append(node.string)
        elif isinstance(node, (str, unicode)):
            data.append(node)
        else:
            assert False, repr(node)
    return u''.join(data)
