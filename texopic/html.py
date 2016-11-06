import urllib

# This module does bit of html escaping and
# provides a minimal way of validating URLs.

# The intent of this module is to reduce surprises
# and to make XSS harder.

# Unfortunately there are so many potential ways to
# do XSS that a simple module such as this cannot
# really ensure the produced markup is safe.

# Not used in whole.. Though left it in here because
# it might turn out useful concept if output pretty-printing
# desired of any kind.
#class Generator(object):
#    def __init__(self):
#        self.output = []
#        self.verbatim = []
#
#    def begin(self, tag, attrs={}, extra=()):
#        data = [tag]
#        for name, value in attrs.items():
#            data.append('{0}="{1}"'.format(
#                name, attr_escape(value)))
#        data.extend(extra)
#        self.output.append('<' + ' '.join(data) + '>')
#
#    def end(self, tag):
#        self.output.append('</' + tag + '>')
#
#    def cr(self):
#        self.verbatim.append('\n')
#        self.output.append('\n')
#
#    def text(self, text):
#        self.verbatim.append(text)
#        self.output.append(body_escape(text))
#
#    def script(self, text):
#        self.output.append('<script>' + text + '</script>')
#
#    #def verify_url(self, url):
#    #    # possibly insufficient.
#    #    return not url.lower().startswith('javascript:')
#
#    def to_string(self):
#        return ''.join(self.output)
#
#    def to_verbatim(self):
#        return ''.join(self.verbatim)
        

# This attr_escape works as long as attributes are correctly quoted.
def attr_escape(attr):
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
