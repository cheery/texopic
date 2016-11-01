import texopic
import sys
from texopic.generic import Env, eval_segment, verbatim
from texopic.toc import Toc
from texopic import html

# hmm....
# #begin{list}
# #item Bananas
# #item Milk
# #item Bread
# #end{list}

class Document(object):
    def __init__(self):
        self.title = u""
        self.toc = Toc()
        self.body = []

def main():
    #print html.attr_escape('aaa <hello a=""> </world>')
    document = Document()
    for nodes in texopic.read_file(sys.argv[1]):
        #print ''.join(map(str, nodes)), '-'
        document.body.extend(
            eval_segment(document, nodes, macros, default_mode))
    print html_template.format(document.title, ''.join(document.body))

def default_mode(document, segment):
    text = segment.text.strip()
    if len(text) > 0:
        yield "<{0}>\n{1}\n</{0}>".format('p', text)
    if segment.pre:
        yield u"<pre>{}</pre>".format(segment.pre.string)

macros = Env()

@macros.modeset("#title", 0)
def macro_title(document, segment):
    text = segment.text.strip()
    document.title = text
    return "<{0}>\n{1}\n</{0}>".format('h1', text)

@macros.modeset("#section", 0)
@macros.modeset("#section", 1)
def macro_section(document, segment, link=None):
    text = segment.text.strip()
    if link is not None:
        link = verbatim(link)
    label, link = document.toc.entry(0, text, link)
    text = "{0}. {1}".format(label, text)
    text += ' <a class="ref" href="#{0}">$</a>'.format(link)
    yield '<{0} id="{2}">\n{1}\n</{0}>'.format('h2', text, link)

@macros.modeset("#subsection", 0)
@macros.modeset("#subsection", 1)
def macro_subsection(document, segment, link=None):
    text = segment.text.strip()
    if link is not None:
        link = verbatim(link)
    label, link = document.toc.entry(1, text, link)
    text = "{0}. {1}".format(label, text)
    text += ' <a class="ref" href="#{0}">$</a>'.format(link)
    yield '<{0} id="{2}">\n{1}\n</{0}>'.format('h3', text, link)

@macros.modeset("#include", 1)
def macro_include(document, segment, path):
    path = verbatim(path) # TODO: make source file relative.
    for nodes in texopic.read_file(path):
        result = eval_segment(document, nodes, segment.macros, default_mode)
        for text in result:
            yield text

@macros.normal("#url", 1)
def macro_function(segment, url):
    return u'<a href="{0}">{0}</a>'.format(
        verbatim(url))

@macros.normal("#href", 2)
def macro_function(segment, url, desc):
    return u'<a href="{0}">{1}</a>'.format(
        verbatim(url),
        segment.inline(desc))

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

if __name__=="__main__":
    main()
