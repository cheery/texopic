from texopic.default_html_env import env
from texopic.generic import Env, process, verbatim
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

env = Env(env)
@env.define("#include", 1)
def env_include(context, path):
    path = verbatim(path) # TODO: make source file relative.
    group = texopic.read_file(path)
    process(context, group)

if __name__=="__main__":
    main()
