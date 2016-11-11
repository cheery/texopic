from texopic.default_html_env import env
from texopic.generic import Env, process, verbatim
from texopic import html
from texopic.toc import Toc
import sys
import texopic

class Document(object):
    def __init__(self):
        self.title = None
        self.description = None
        self.toc = Toc()

template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
{0}</head>
<body>
{1}</body>
</html>"""

style = """
body { max-width: 75ex }
body > pre { border: 1px solid #cfcfcf; padding: 1em 4ex }
h2       > .ref { visibility: hidden; text-decoration: underline; }
h2:hover > .ref { visibility: visible !important }
h3       > .ref { visibility: hidden; text-decoration: underline; }
h3:hover > .ref { visibility: visible !important }

.sourcetable pre { margin: 0; }
.sourcetable .linenos { padding-left: 1ex; padding-right: 1ex;
    border-right: 1px solid black; }


""".strip()

def main():
    group = texopic.read_file(sys.argv[1])
    document = Document()
    head = html.Block([])
    body = html.Block(env.vcall(group, document))

    if document.title is not None:
        head.append(html.Node('title', [document.title]))
    if document.description is not None:
        head.append(html.Node('meta', None, {
            'name':'description',
            'content':document.description,
        }, slash=False))
    head.append(html.Node('style', [html.Raw(style)]))
    head.append(html.Node('link', None, {
        "rel": "stylesheet",
        "type": "text/css",
        "href": html.URL("pygments-style.css"),
    }))
    print template.format(
        html.stringify(head),
        html.stringify(body))

env = Env(env)
@env.define("#include", 1)
def env_include(context, path):
    path = verbatim(path) # TODO: make source file relative.
    group = texopic.read_file(path)
    process(context, group)

@env.define("#description", 0)
def env_description(context):
    @context.next_group
    def _build_description_(context, group):
        context.document.description = verbatim(group)

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
@env.define("#sample", 0)
def env_sample(context):
    @context.next_group
    def _build_sample_(context, group, code=""):
        name = verbatim(group).strip() or "python"
        lexer = get_lexer_by_name(name, stripall=True)
        formatter = HtmlFormatter(linenos=True, cssclass="source")
        context.emit(html.Raw(highlight(code, lexer, formatter)))
    _build_sample_.capture_pre = True

# heheehe.
@env.define("#include_code", 2)
def env_include_python_code(context, lexer_name, path):
    name = verbatim(lexer_name).strip() or "python"
    path = verbatim(path) # TODO: make source file relative?
    with open(path, "r") as fd:
        code = fd.read()
        lexer = get_lexer_by_name(name, stripall=True)
        formatter = HtmlFormatter(linenos=True, cssclass="source")
        context.emit(html.Raw(highlight(code, lexer, formatter)))


if __name__=="__main__":
    main()
