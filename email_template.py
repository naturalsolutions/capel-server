class EmailTemplate(object):
    def __init__(self, template='', values={}):
        self.template = template
        self.values = values

    def render(self):
        content = ''
        with open(self.template, 'r') as t:
            content = t.read()
            for k, v in self.values.items():
                content = content.replace('{{{{{}}}}}'.format(k), v)
        return str(content)
