from structures import Escape, Macro, Pre
# Generic functionality to create a texopic processor.
#
# This has changed a lot over time. It will likely still
# change a bit, but I don't know when.
# It feels pretty good now.
# There is example of use in texopic2html.py -script.

class Env(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.scope = {}

    def define(self, *key):
        def _deco_(fn):
            self.scope[key] = fn
            return fn
        return _deco_

    def lookup(self, *key):
        if key in self.scope:
            return self.scope[key]
        elif self.parent:
            return self.parent.lookup(*key)
        return None

    def hcall(env, group, document):
        context = Context(env, Horizontal(), document)
        process(context, group)
        while context.mode.parent != None:
            mode = context.mode
            mode.build(context, context.mode.data)
            context.mode = mode.parent
        return context.mode.data

    def vcall(env, group, document):
        context = Context(env, Vertical(), document)
        process(context, group)
        while context.mode.parent != None:
            mode, context.mode = context.mode, context.mode.parent
            mode.build(context, mode.data)
        return context.mode.data

def process(context, group):
    for node in group:
        if isinstance(node, Escape):
            context.emit_text(node.character)
        elif isinstance(node, (str, unicode)):
            if node.isspace():
                context.emit_space()
            else:
                context.emit_text(node)
        elif isinstance(node, Macro):
            try:
                macro_process(context, node.name, node.groups)
            except Suspend as s:
                context.emit_text(node.name)
                for subgroup in node.groups:
                    context.emit_text('{')
                    process(context, subgroup)
                    context.emit_text('}')
        elif isinstance(node, Pre):
            context.emit_pre(node.string)
        else:
            context.emit_text(repr(node))

def macro_process(context, name, groups):
    if name == '':
        context.end_group()
    elif name == "#begin":
        if len(groups) >= 1:
            block_name = verbatim(groups[0])
            args = groups[1:]
            macro = context.env.lookup(":" + block_name, len(args))
            if macro is None:
                raise Suspend()
            else:
                context.goto_vertical()
                context.mode = Vertical(context.mode, block_name,
                    **macro(context, *args))
    elif name == "#end":
        if len(groups) == 0:
            base, cake = collapse_frame(context)
            base.build(context, cake)
        else:
            block_name = verbatim(groups[0])
            if context.in_cake(block_name):
                while context.in_cake(block_name):
                    base, cake = collapse_frame(context)
                    base.build(context, cake)
            else:
                raise Suspend()
    else:
        macro = context.env.lookup(name, len(groups))
        if macro is None:
            raise Suspend()
        else:
            output = macro(context, *groups)
            if output is not None:        # makes it bit simpler to write
                context.emit_text(output) # to write common macros.

def collapse_frame(context):
    mode = context.mode
    while mode is not None and not isinstance(mode, Vertical):
        mode = mode.parent
    if isinstance(mode, Vertical) and mode.parent is not None:
        cake = Cake(context, context.mode)
        context.mode = mode.parent
        return mode, cake
    raise Suspend()

class Cake(object):
    def __init__(self, context, chain):
        self.context = context
        self.chain = chain

    @property
    def is_empty(self):
        if self.is_group:
            return len(self.chain.data) == 0
        elif isinstance(self.chain, Vertical):
            return len(self.chain.data) == 0

    @property
    def is_group(self):
        if isinstance(self.chain, Horizontal):
            return len(self.chain.parent.data) == 0
        return False

    def as_group(self):
        assert self.is_group
        data = self.chain.data
        self.chain.data = []
        if self.context.mode is self.chain:
            self.context.mode = self.chain.parent
        self.chain = None
        return data

    def as_list(self):
        mode = self.context.mode
        self.context.mode = self.chain
        self.context.goto_vertical()
        if mode is self.chain:
            self.chain = self.context.mode
        else:
            self.chain = self.context.mode
            self.context.mode = mode
        data = self.chain.data
        self.chain.data = []
        self.chain = None
        return data

class Vertical(object):
    def __init__(self, parent=None, name=None, build=None, block=None):
        self.parent = parent
        self.data = []
        self.name = name
        self.build = build
        self.block = block

    def emit(self, value):
        self.data.append(value)

    is_restricted = False

    def builder(self, fn):
        self.build = fn

class Horizontal(object):
    def __init__(self, parent=None, build=None):
        self.parent = parent
        self.data = []
        self.ended = False
        self.space = False
        self.capture_pre = False
        self.build = build

    def emit(self, value):
        if self.space:
            self.data.append(' ')
        self.space = False
        self.data.append(value)

    @property
    def block(self):
        return self.parent.block if self.parent is not None else None

    @property
    def is_restricted(self):
        return not isinstance(self.parent, Vertical)

    def builder(self, fn):
        self.build = fn

class Context(object):
    def __init__(self, env, mode, document):
        self.env = env
        self.mode = mode
        self.document = document

    def emit(self, value):
        self.goto_vertical()
        self.mode.emit(value)

    def emit_text(self, value):
        if not isinstance(self.mode, Horizontal) or self.mode.ended:
            self.next_group(self.env.lookup("paragraph"))
        self.mode.emit(value)

    def emit_space(self):
        if isinstance(self.mode, Horizontal) and len(self.mode.data) > 0:
            self.mode.space = True

    def emit_pre(self, string):
        if isinstance(self.mode, Horizontal):
            if self.mode.capture_pre:
                mode, self.mode = self.mode, self.mode.parent
                mode.build(self, mode.data, string)
            else:
                self.goto_vertical()
        if self.mode.is_restricted:
            self.mode.emit(("##\n"+string).replace('\n', '    '))
        else:
            self.env.lookup("preformat")(self, string)

    def next_group(self, builder): # suspended in restricted horizontal mode.
        self.goto_vertical()
        self.mode = Horizontal(self.mode, builder)
        return self.mode

    def goto_vertical(self):
        if self.mode.is_restricted:
            raise Suspend()
        if isinstance(self.mode, Horizontal):
            mode, self.mode = self.mode, self.mode.parent
            mode.build(self, mode.data)
        
    # does not yet .build() it. But causes the next emit to
    # create new paragraph.
    def end_group(self):  # ignored in restricted horizontal mode.
        if self.mode.is_restricted:
            return
        if isinstance(self.mode, Horizontal):
            self.mode.ended = True

    def in_cake(self, name):
        mode = self.mode
        while mode is not None:
            if isinstance(mode, Vertical) and mode.name == name:
                return True
            mode = mode.parent
        return False
    
    @property
    def block(self):
        return self.mode.block

    def get_cake(self):
        return Cake(self, self.mode)

    def hcall(self, group):
        return self.env.hcall(group, self.document)

    def vcall(self, group):
        return self.env.vcall(group, self.document)

# Raise this when you don't want to do something.
class Suspend(Exception):
    pass

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
