
class CustomDict(dict):
    ''' Allows for Dot Notation Access to Dictionary References '''

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
