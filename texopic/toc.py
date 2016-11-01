# Helper to generate table of contents

def default_labeling():
    index = 1
    while True:
        yield str(index)
        index += 1

class Toc(object):
    def __init__(self, separator='.', labeling=default_labeling):
        self.separator = separator
        self.labeling = labeling
        self.prefix = []
        self.stack  = []
        self.data = []

    def entry(self, depth, text, link=None):
        while depth > len(self.stack):
            labelgen = self.labeling()
            self.stack.append(labelgen)
            self.prefix.append(labelgen.next())
        if depth == len(self.stack):
            labelgen = self.labeling()
            self.stack.append(labelgen)
            self.prefix.append(labelgen.next())
        else:
            while depth + 1 < len(self.stack):
                self.stack.pop()
                self.prefix.pop()
            self.prefix[-1] = self.stack[-1].next()
        label = self.separator.join(self.prefix)
        if link is None:
            link = label
        self.data.append((label, link, text))
        return label, link
