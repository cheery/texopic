from texopic.generic import *
from texopic import html
from texopic.toc import Toc
import sys
import texopic

class Document(object):
    def __init__(self):
        self.title = None
        self.toc = Toc()

template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{0}</head>
<body>
{1}</body>
</html>"""

style = """
body { max-width: 75ex }
pre { border: 1px solid #cfcfcf; padding: 1em 4ex }
h2       > .ref { visibility: hidden; text-decoration: underline; }
h2:hover > .ref { visibility: visible !important }
h3       > .ref { visibility: hidden; text-decoration: underline; }
h3:hover > .ref { visibility: visible !important }
""".strip()

def main():
    group = texopic.read_file(sys.argv[1])
    document = Document()
    head = html.Block([])
    body = html.Block(env.vcall(group, document))

    if document.title is not None:
        head.append(html.Node('title', [document.title]))
    head.append(html.Node('style', [style]))
    print template.format(
        html.stringify(head),
        html.stringify(body))

env = Env()

@env.define("preformat")
def env_pre(context, string):
    context.emit(html.Node('pre', [string]))

@env.define("paragraph")
def env_group(context, group):
    context.emit(html.Node('p', group))

@env.define("#title", 0)
def env_title(context):
    @context.next_group
    def _build_title_(context, group):
        heading = html.Node('h1', group)
        context.document.title = heading.verbatim()
        context.emit(heading)

@env.define("#section", 0)
@env.define("#section", 1)
def env_section(context, link_=None):
    if link_ is not None:
        link_ = verbatim(link_)
    @context.next_group
    def _build_section_(context, group):
        heading = html.Node('h2', group)

        label, link = context.document.toc.entry(0, heading.verbatim(), link_)
        heading.attrs['id'] = link
        heading.insert(0, "{0}. ".format(label))
        heading.extend([" ", html.Node('a', ["$"], {
            "class": "ref",
            "href": html.URL('#' + link)
        })])
        context.emit(heading)

@env.define("#subsection", 0)
@env.define("#subsection", 1)
def env_section(context, link_=None):
    if link_ is not None:
        link_ = verbatim(link_)
    @context.next_group
    def _build_section_(context, group):
        heading = html.Node('h3', group)

        label, link = context.document.toc.entry(1, heading.verbatim(), link_)
        heading.attrs['id'] = link
        heading.insert(0, "{0}. ".format(label))
        heading.extend([" ", html.Node('a', ["$"], {
            "class": "ref",
            "href": html.URL('#' + link)
        })])
        context.emit(heading)
 
@env.define("#include", 1)
def env_include(context, path):
    path = verbatim(path) # TODO: make source file relative.
    group = texopic.read_file(path)
    process(context, group)

@env.define("#bold", 1)
def env_bold(context, group):
    return html.Node('b', context.hcall(group))

@env.define("#comment", 0)
def env_comment(context):
    @context.next_group
    def _build_(context, group):
        pass

@env.define(":comment", 0)
def env_begin_comment(context):
    def _build_(context, cake):
        pass
    return {"build": _build_, "block": None}

@env.define(":itemize", 0)
def env_begin_itemize(context):
    block = Itemize()
    def _build_(context, cake):
        block.item(cake)
        context.emit(html.Node('ul', block.data))
    return {"build": _build_, "block": block}

@env.define(":enumerate", 0)
def env_begin_itemize(context):
    block = Itemize()
    def _build_(context, cake):
        block.item(cake)
        context.emit(html.Node('ol', block.data))
    return {"build": _build_, "block": block}

@env.define("#item", 0)
def env_item(context):
    if isinstance(context.mode.block, Itemize):
        context.block.item(context.get_cake())
    else:
        raise Suspend()

class Itemize(object):
    def __init__(self):
        self.data = []

    def item(self, cake):
        if cake.is_empty and len(self.data) == 0:
            pass # the first #item
        elif cake.is_group:
            self.data.append(html.Node('li', cake.as_group()))
        else:
            self.data.append(html.Node('li', cake.as_list()))

@env.define("#image", 1)
def env_image(context, src):
    return html.Node('img', attrs={
        "src": html.URL(verbatim(src))
    })

@env.define("#image", 2)
def env_image_2(context, src, desc):
    return html.Node('img', attrs={
        "src": html.URL(verbatim(src)),
        "alt": verbatim(desc)
    })

@env.define("#url", 1)
@env.define("#href", 1)
def env_url(context, url):
    url = html.URL(verbatim(url))
    return html.Node('a', [url], {"href": url})

@env.define("#href", 2)
def env_href(context, url, desc):
    url = html.URL(verbatim(url))
    return html.Node('a', context.hcall(desc), {"href": url})

if __name__=="__main__":
    main()
