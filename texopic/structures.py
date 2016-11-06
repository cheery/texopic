# generic.py had to be aware about
# structures present, so put them here.

class Escape(object):
    def __init__(self, character, which='uni'):
        self.character = character
        self.which = which

    def __str__(self):
        return self.character

    def __repr__(self):
        return "Escape({!r})".format(self.character)

class Macro(object):
    def __init__(self, name):
        self.name = name
        self.groups = []

    def __str__(self):
        return ";" + self.name + ''.join(
            '{'+''.join(map(str, group))+'}'
            for group in self.groups) + ";"

    def __repr__(self):
        return "Macro({!r})".format(self.name)

class Pre(object):
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return ";##\n"

    def __repr__(self):
        return "Pre(...)"
