from texopic.generic import Env, process, verbatim
import html

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
        section_toc(context.document.toc, 0, heading, link_)
        context.emit(heading)

@env.define("#subsection", 0)
@env.define("#subsection", 1)
def env_section(context, link_=None):
    if link_ is not None:
        link_ = verbatim(link_)
    @context.next_group
    def _build_section_(context, group):
        heading = html.Node('h3', group)
        section_toc(context.document.toc, 1, heading, link_)
        context.emit(heading)

def section_toc(toc, depth, heading, link):
    label, link = toc.entry(depth, heading.verbatim(), link)
    heading.attrs['id'] = link
    heading.insert(0, "{0}. ".format(label))
    heading.extend([" ", html.Node('a', ["$"], {
        "class": "ref",
        "href": html.URL('#' + link)
    })])

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
