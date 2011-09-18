class Data(object):

    def __init__(self, prompt=None, default=None, values=None,
                 kind=None, decode=None):
        self.prompt = prompt
        self.default = default
        self.values = values
        self.kind = kind
        self._decode = decode

    def decode(self, value):
        if self._decode:
            return self._decode(value)
        return value


class Boolean(Data):

    def __init__(self, prompt=None, default=False):
        Data.__init__(self, prompt, self._encode(default),
                      [self._encode(True), self._encode(False)])

    def _encode(self, value):
        if value:
            return 'yes'
        return 'no'

    def decode(self, value):
        if value.lower() in ('yes', '1', 'true'):
            return True
        return False


def show_dialog(askdata, actions, confs={}, optionals={}, initial_asking=True):
    result = {}
    if initial_asking:
        for name, conf in confs.items():
            result[name] = askdata(conf)
    actions.append('batchset')
    names = list(actions)
    names.extend(optionals.keys())
    names.extend(confs.keys())
    base_question = Data('Choose what to do: ',
                         default=actions[0], values=names)
    batchset_question = Data('Batch sets: ')
    while True:
        response = askdata(base_question)
        if response == '':
            response = base_question.default
        elif response == 'batchset':
            sets = askdata(batchset_question)
            for key, value in _parse_batchset(sets).items():
                if key.endswith(':'):
                    key = key[:-1]
                if key in names:
                    conf = confs.get(key, optionals.get(key))
                    result[key] = value
        elif response in actions:
            break
        else:
            if response in confs:
                conf = confs[response]
            else:
                conf = optionals[response]
            oldvalue = result.get(response, None)
            result[response] = askdata(conf, starting=oldvalue)
    decoded = {}
    all_confs = dict(confs)
    all_confs.update(optionals)
    for key in all_confs:
        conf = all_confs.get(key)
        if key in result:
            decoded[key] = conf.decode(result[key])
        else:
            decoded[key] = conf.decode(conf.default)
    return response, decoded


def _parse_batchset(sets):
    result = []
    multiline = False
    for line in sets.splitlines(True):
        if line[0].isspace():
            if multiline:
                result[-1][1] += line[1:]
        else:
            if not line.strip():
                continue
            multiline= False
            tokens = line.split(None, 1)
            value = ''
            if len(tokens) > 1:
                result.append([tokens[0], tokens[1].rstrip('\r\n')])
            else:
                multiline = True
                result.append([tokens[0], ''])
    return dict(result)
