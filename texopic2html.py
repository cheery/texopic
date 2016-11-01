import texopic
import sys
from texopic.generic import Env, eval_segment, verbatim

class Document(object):
    def __init__(self):
        self.title = u""
        self.h2_count = 0
        self.body = []

def main():
    document = Document()
    for nodes in texopic.read_file(sys.argv[1]):
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
def macro_section(document, segment):
    document.h2_count += 1
    tag = str(document.h2_count)
    text = "{0}. ".format(document.h2_count) + segment.text.strip()
    text += ' <a class="ref" href="#{0}">$</a>'.format(tag)
    yield '<{0} id="{2}">\n{1}\n</{0}>'.format('h2', text, tag)

@macros.modeset("#subsection", 0)
def macro_subsection(document, segment):
    yield "<{0}>\n{1}\n</{0}>".format('h3', segment.text.strip())

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
h2       > .ref {{ visibility: hidden; text-decoration: none; }}
h2:hover > .ref {{ visibility: visible !important }}
</style>
</head>
<body>
{1}
</body>
</html>"""

if __name__=="__main__":
    main()
