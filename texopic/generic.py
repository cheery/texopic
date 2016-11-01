from structures import Escape, Macro, Pre
# Generic functionality to create a texopic processor.
#
# Will likely change a bit. Has example of use in
# texopic2html.py -script.

class Env(object):
    def __init__(self):
        self.macros = {}

    def __contains__(self, index):
        return index in self.macros

    def __getitem__(self, index):
        return self.macros[index]

    def normal(self, name, argc):
        def _deco_(fn):
            self.macros[(name, argc)] = fn
            return fn
        return _deco_

    def modeset(self, name, argc):
        def _deco_(fn):
            self.macros[(name, argc)] = modeset(fn, name)
            return fn
        return _deco_

def eval_segment(document, nodes, macros, default_mode):
    if len(nodes) > 0 and isinstance(nodes[-1], Pre):
        pre = nodes.pop()
    else:
        pre = None
    segment = Segment(document, pre, macros)
    for node in nodes:
        shift(segment, node)
    return segment.resolve(default_mode)

def modeset(fn, name):
    def modeset_deco(segment, *args):
        if segment.mode is None:
            segment.mode = (fn, args)
        else:
            return macro_verbatim(name, args)
    modeset_deco.__name__ = fn.__name__
    return modeset_deco

class Segment(object):
    def __init__(self, document, pre, macros, parent=None):
        self.document = document
        self.parent = parent
        self.pre = pre
        self.mode = None # default
        self.data = []
        self.macros = macros

    def inline(self, nodes):
        segment = Segment(self.document, None, self.macros, self)
        segment.mode = True
        for node in nodes:
            shift(segment, node)
        return u''.join(segment.data)

    @property
    def text(self):
        return u''.join(self.data)

    def resolve(self, default_mode_fn):
        if self.mode is not None:
            fn, args = self.mode
            return fn(self.document, self, *args)
        else:
            return default_mode_fn(self.document, self)

def shift(segment, node):
    if isinstance(node, Escape):
        shift(segment, node.character)
    elif isinstance(node, Macro):
        name = (node.name, len(node.groups))
        if name in segment.macros:
            result = segment.macros[name](segment, *node.groups)
            if result is not None:
                segment.data.append(result)
        else:
            shift(segment, node.name)
            for group in node.groups:
                shift(segment, u"{")
                for node in group:
                    shift(segment, node)
                shift(segment, u"}")
    else:
        assert isinstance(node, (str, unicode)), repr(node)
        segment.data.append(node)

def verbatim(nodes):
    data = []
    for node in nodes:
        if isinstance(node, Escape):
            data.append(node.character)
        elif isinstance(node, Macro):
            data.append(macro_verbatim(node.name, node.groups))
        else:
            assert isinstance(node, (str, unicode)), repr(node)
            data.append(node)
    return u''.join(data)

def macro_verbatim(name, groups):
    data = [name]
    for group in groups:
        data.append(u"{")
        data.append(verbatim(group))
        data.append(u"}")
    return u''.join(data)
