import printer
from StringIO import StringIO
#import urllib

# This module does bit of html escaping and
# provides a minimal way of validating URLs.

# The intent of this module is to reduce surprises
# and to make XSS harder.

# Unfortunately there are so many potential ways to
# do XSS that a simple module such as this cannot
# really ensure the produced markup is safe.

def stringify(obj, margin=70):
    scan = printer.Scanner(StringIO(), margin)
    stringify_(scan, obj)
    scan.finish()
    return scan.printer.fd.getvalue()

def stringify_(scan, obj):
    if obj == ' ':
        scan.blank(' ', forceable=False)
    elif isinstance(obj, (str, unicode)):
        scan(body_escape(obj))
    else:
        obj.stringify(scan)

def verbatim_(obj):
    if isinstance(obj, (str, unicode)):
        return obj
    else:
        return obj.verbatim()

class Block(object):
    def __init__(self, data):
        self.data = data

    def stringify(self, scan):
        for x in self.data:
            stringify_(scan, x)

    def verbatim(self):
        return ''.join(map(verbatim_, self.data))

    def append(self, node):
        self.data.append(node)
    
    def extend(self, nodes):
        self.data.extend(nodes)

    def insert(self, index, node):
        self.data.insert(index, node)

class URL(object):
    def __init__(self, href):
        self.href = href

    def stringify(self, scan):
        scan(body_escape(self.href))

    def verbatim(self):
        return self.href

class Node(object):
    def __init__(self, tag, data=None, attrs=None, extra=(), space_sensitive=None, raw=False):
        self.tag = tag
        self.data = data
        self.attrs = {} if attrs is None else attrs
        self.extra = extra
        self.space_sensitive = (self.tag == 'pre') if space_sensitive else space_sensitive
        self.raw = raw

    def stringify(self, scan):
        scan('<').left().left()
        scan(self.tag)
        for name, value in self.attrs.items():
            scan.blank(' ', 2)
            scan('{0}="{1}"'.format(
                name, attr_escape(value)))
        for item in self.extra:
            scan.blank(' ', 2)
            scan(item)
        scan.right()
        if self.data is None:
            scan('/>').blank('').right()
        else:
            scan('>').left()
            if not self.space_sensitive:
                scan.blank('')
            if self.raw:
                scan(self.data)
            else:
                for x in self.data:
                    stringify_(scan, x)
            if not self.space_sensitive:
                scan.blank('')
            scan.right()('</')
            scan(self.tag)
            scan('>').right()

    def verbatim(self):
        if self.data is None:
            return ''
        return ''.join(map(verbatim_, self.data))

    def append(self, node):
        self.data.append(node)
    
    def extend(self, nodes):
        self.data.extend(nodes)

    def insert(self, index, node):
        self.data.insert(index, node)

# This attr_escape works as long as attributes are correctly quoted.
def attr_escape(attr):
    if isinstance(attr, URL):
        return attr_escape(attr.href)
    return "".join(
        c if c in attr_whitelist or ord(c) >= 256 else "&#x%02X;" % ord(c)
        for c in attr)

attr_whitelist = (
    "!*'();:@=+$,/?#[] "
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789-_.~")

# And this is perfectly sufficient for escaping the body.
def body_escape(text):
    return "".join(escape_table.get(c, c) for c in text)

escape_table = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;"}


# If you ever user this generator on user-generated content:
# Validate URLs properly.
# Do not let users insert custom attributes or tags.
# Also be careful with Angular.js and such that re-interpret HTML. 


# This thing doesn't handle URLs properly. It could, but there are few
# questions about what to do about them.

# The URLs scheme should be checked against a whitelist to check that an
# URL is not used to attack the user.


# Here was a tryout, but I'm thinking I'm overthinking it.
#def validate_url(url, scheme_whitelist):
#    if scheme_whitelist is None:
#        scheme_whitelist = default_scheme_whitelist
#    scheme = urlparse(url).scheme
#    return scheme == '' or scheme in protocol_whitelist

# Also this doesn't increase safety.
# def validate_tag(x):
#     return bool(re.match(r"^[0-9a-zA-Z\-_]+$", x))

# Another alternative. possibly insufficient
#    #def verify_url(self, url):
#    #    return not url.lower().startswith('javascript:')
