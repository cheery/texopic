import texopic
import sys
#from texopic.generic import Env, verbatim, Buffer, invoke
from texopic.generic import *
from texopic.toc import Toc
from texopic import html

html_template = u"""<html>
<head>
<meta charset="utf-8">
<title>{0}</title>
<style>
body {{ max-width: 75ex }}
pre {{ border: 1px solid #cfcfcf; padding: 1em 4ex }}
h2       > .ref {{ visibility: hidden; text-decoration: underline; }}
h2:hover > .ref {{ visibility: visible !important }}
h3       > .ref {{ visibility: hidden; text-decoration: underline; }}
h3:hover > .ref {{ visibility: visible !important }}
</style>
</head>
<body>
{1}
</body>
</html>"""

class Document(object):
    def __init__(self):
        self.title = u""
        self.toc = Toc()

def main():
    group = texopic.read_file(sys.argv[1])
    document = Document()
    context = invoke(group, document,
        preformat = (lambda a: HTMLWrap([a], 'pre')),
        paragraph = (lambda p: HTMLWrap(p, 'p', True)),
        do_macro = do_macro,
        do_begin = do_begin)
    print html_template.format(
        document.title,
        HTML(context.pull_vertical()))

do_macro = Env()
do_begin = Env()

@do_macro.define("#bold", 1)
def macro_bold(context, group):
    context = context.invoke(group)
    if context.is_horizontal:
        return HTMLWrap(context.pull_horizontal(), 'b')
    else:
        # TODO, mark bold vertical
        return HTMLWrap(context.pull_vertical(), 'div')

@do_macro.define("#comment", 0)
def macro_comment(context):
    context.builder.next_group(lambda group: '')

@do_begin.define("comment", 0)
def begin_comment(context):
    return context.begin(Ignorer())

class Ignorer(object):
    def __init__(self):
        pass

    def end(self, context):
        return ""

@do_macro.define("#image", 1)
def macro_image(context, src):
    return HTMLStub('img',
        src=URL(verbatim(src)))

@do_macro.define("#image", 2)
def macro_image_2(context, src, alt):
    return HTMLStub('img',
        src=URL(verbatim(src)),
        alt=verbatim(alt))

@do_macro.define("#item", 0)
def macro_item(context):
    if isinstance(context.block, Itemize):
        context.block.add(context)
        return ""

@do_begin.define("itemize", 0)
def begin_itemize(context):
    return context.begin(Itemize('ul'))

@do_begin.define("enumerate", 0)
def begin_itemize(context):
    return context.begin(Itemize('ol'))

class Itemize(object):
    def __init__(self, tag):
        self.tag = tag
        self.data = []

    def add(self, context):
        if context.is_horizontal:
            if len(self.data) == 0 and len(context.builder.group) == 0:
                return
            self.data.append( HTMLWrap(context.pull_horizontal(), 'li', True))
        else:
            self.data.append( HTMLWrap(context.pull_vertical(), 'li', True))
    
    def end(self, context):
        self.add(context)
        return HTMLWrap(self.data, self.tag)

@do_macro.define("#title", 0)
def macro_title(context):
    context.builder.next_group(make_title, context.document)
    return ""

def make_title(group, document):
    heading = HTMLWrap(group, 'h1', True)
    document.title = heading.verbatim()
    return heading

@do_macro.define("#section", 0)
@do_macro.define("#section", 1)
def macro_section(context, link=None):
    if link is not None:
        link = verbatim(link)
    context.builder.next_group(make_section_heading,
        context.document, 0, link, 'h2')
    return ''

@do_macro.define("#subsection", 0)
@do_macro.define("#subsection", 1)
def html_subsection(context, link=None):
    if link is not None:
        link = verbatim(link)
    context.builder.next_group(make_section_heading,
        context.document, 1, link, 'h3')
    return ''

def make_section_heading(body, document, depth, link, tag):
    label, link = document.toc.entry(depth, body, link)
    return HTMLWrap( # there's ugly, then there's this.
        ["{0}. ".format(label)] +
        body + [" ", HTMLWrap(["$"], 'a', **{
            'class':"ref", 'href':URL('#'+link)
        })],
        tag, brk=True, id=link)

@do_macro.define("#include", 1)
def macro_include(context, path):
    path = verbatim(path) # TODO: make source file relative.
    group = texopic.read_file(path)
    context.builder.next_group(context.paragraph)
    context.builder.vertical.extend(
        context.invoke(group).pull_vertical()
    )
    return ""


@do_macro.define("#url", 1)
def macro_url(context, url):
    url = URL(verbatim(url))
    return HTMLWrap([url], 'a', href=url)

@do_macro.define("#href", 2)
def macro_href(context, url, desc):
    url = URL(verbatim(url))
    context = context.invoke(desc)
    if context.is_horizontal:
        return HTMLWrap(context.pull_horizontal(), 'a', href=url)
    else:
        return HTMLWrap(context.pull_vertical(), 'a', href=url)


class URL(object):
    def __init__(self, href):
        self.href = href

    def __str__(self):
        return self.href


class HTML(object):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return ''.join(
            html.body_escape(x)
            if isinstance(x, (str, unicode)) else str(x)
            for x in self.data)

    def verbatim(self):
        return ''.join(
            x if isinstance(x, (str, unicode)) else x.verbatim()
            for x in self.data)

class HTMLWrap(object):
    def __init__(self, data, tag, brk=False, extra=(), **attrs):
        self.data = data
        self.tag = tag
        self.brk = brk
        self.extra = extra
        self.attrs = attrs

    def __str__(self):
        if self.brk:
            output = [
                open_tag(self.tag, self.attrs, self.extra), '\n',
                ''.join(
                    html.body_escape(x)
                    if isinstance(x, (str, unicode)) else
                    str(x)
                    for x in self.data),
                '\n</', self.tag, '>']
        else:
            output = [
                open_tag(self.tag, self.attrs, self.extra),
                ''.join(
                    html.body_escape(x)
                    if isinstance(x, (str, unicode)) else
                    str(x)
                    for x in self.data),
                '</', self.tag, '>']
        return ''.join(output)

    def verbatim(self):
        return ''.join(
            x if isinstance(x, (str, unicode)) else x.verbatim()
            for x in self.data)

class HTMLStub(object):
    def __init__(self, tag, extra=(), **attrs):
        self.tag = tag
        self.extra = extra
        self.attrs = attrs

    def __str__(self):
        return open_tag(self.tag, self.attrs, self.extra, '/>')
    
    def verbatim(self):
        return ''

def open_tag(tag, attrs, extra, end='>'):
    data = [tag]
    for name, value in attrs.items():
        data.append('{0}="{1}"'.format(
            name, html.attr_escape(str(value))))
    data.extend(extra)
    return '<' + ' '.join(data) + end

if __name__=="__main__":
    main()
