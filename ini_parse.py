import re
from cStringIO import StringIO
import ConfigParser
import logging
from pprint import pprint

def ini_to_dict(ini):
    '''
    Convert an .ini file content into a dictionary (actually, a dictionary of
    dictionaries). Many functions in this module work on that resulting
    dictionary, corresponding to the represented file. You should understand
    the mapping. Into the resulting dictionary of dictionaries, first level
    keys are the sections, second level keys are the options inside each
    section. This is obsoleted by configparser interface in python 3 standard
    library.

    >>> ini = """
    ... [core]
    ... log = value
    ... main_loop_timeout = 5.9
    ...
    ... [other section]
    ... other variable = value
    ... """
    >>> dict_ = {
    ...     'core': {
    ...         'log': 'value',
    ...         'main_loop_timeout': '5.9',
    ...     },
    ...     'other section': {
    ...         'other variable': 'value',
    ...     },
    ... }
    >>> ini_to_dict(ini) == dict_
    True
    '''
    parser = ConfigParser.ConfigParser()
    fp = StringIO(ini)
    parser.readfp(fp)
    options = {}
    for section in parser.sections():
        options[section] = dict(parser.items(section))
    return options

def dict_to_ini(dict_):
    '''
    >>> dict_ = {'core': {'log': 'value', 'main_loop_timeout': '5.9'}, 'other section': {'other variable': 'value'}}
    >>> dict_ == ini_to_dict(dict_to_ini(dict_))
    True
    '''
    parser = ConfigParser.ConfigParser()
    fp = StringIO()
    for sk, sv in dict_.items():
        parser.add_section(sk)
        for ok, ov in sv.items():
            parser.set(sk, ok, ov)
    parser.write(fp)
    return fp.getvalue()

def apply_templates(providers, users, keyword='template'):
    '''
    In an .ini file with sections defining objects, one may wish to create
    several sections from a common template, just overriding some of the
    parameters into the source template.

    >>> providers = {
    ...  'template_name': {'host'      : '111.111.111.111',
    ...                             'port'      : '1234',
    ...                             'configure' : 'a',
    ...  }
    ... }
    >>> users = {
    ...  'user one': {'template' : 'template_name',
    ...               'extra'    : 'extra value'},
    ...  'user two': {'template' : 'template_name',
    ...               'host'     : '222.222.222.222',
    ...               'other'    : 'other value'},
    ... }
    >>> result = {
    ... 'user one': {'configure': 'a',
    ...              'extra': 'extra value',
    ...              'host': '111.111.111.111',
    ...              'port': '1234'},
    ... 'user two': {'configure': 'a',
    ...              'host': '222.222.222.222',
    ...              'other': 'other value',
    ...              'port': '1234'}}
    >>> apply_templates(providers, users) == result
    True
    >>> r = apply_templates({}, users)
    Traceback (most recent call last):
       ...
    Exception: Option "template = template_name" defined in section "user one", but section "template template_name" is missing
    '''
    result = users.copy()
    for name, options in users.items():
        if keyword in options:
            provider_name = options[keyword]
            if provider_name not in providers:
                raise Exception('Option "{keyword} = {0}" defined in section "{1}", but section "{keyword} {0}" is missing'.format(provider_name, name, keyword=keyword))
            template = providers[provider_name].copy()
            template.update(options)
            del template[keyword]
            result[name] = template
    return result

def parse_multioption(options, prefix, keep=False):
    '''
    Filter and parse options based on a prefix, in order to build an user
    defined dictionary.

    >>> options={
    ...  'bind_timeout': '30',
    ...  'ini_dict__key1': 'val1',
    ...  'ini_dict__key2': 'val2',
    ...  'ini_dict__key3': 'val3',
    ...  'enquire_maxfailures': '1',
    ...  'enquire_timeout': '120',
    ...  'another_dict___keyA': 'valA',
    ...  'another_dict___keyB': 'valB',
    ... }
    >>> ini_dict = {
    ... 'key3': 'val3',
    ... 'key2': 'val2',
    ... 'key1': 'val1',
    ... }
    >>> parse_multioption(options, 'ini_dict__') == ini_dict
    True
    >>> another_dict = {
    ... 'keyB': 'valB',
    ... 'keyA': 'valA',
    ... }
    >>> parse_multioption(options, 'another_dict___') == another_dict
    True
    '''
    pattern = '{p}(.+)'.format(p=prefix)
    parsed = {}
    for k,v in options.items():
        match = re.search(pattern, k)
        if match:
            if keep:
                new_key = k
            else:
                new_key = match.group(1)
            parsed[new_key] = v
    return parsed

def bool_conversion(v):
    '''
    >>> b = bool_conversion
    >>> b('True'), b('False')
    (True, False)
    >>> b('true'), b('false')
    (True, False)
    >>> b('foo')
    Traceback (most recent call last):
    ...
    ValueError: invalid literal for bool_conversion(): 'foo'
    '''
    if v.title() == 'True':  return True
    if v.title() == 'False': return False
    raise ValueError('invalid literal for bool_conversion(): {0!r}'.format(v))

def autoconvert_type(value):
    '''
    Convert a string to a builtin type trying to guess the type.
    
    >>> a = autoconvert_type
    >>> a('1')
    1
    >>> a('a')
    'a'
    >>> a('False')
    False
    '''
    for conversion in (int, float, bool_conversion, str):
        try: return conversion(value)
        except ValueError: pass

def selective_update(default, new=None, check_type=False):
    '''
    Useful for update an object's default values with parameters that come from
    a configuration section, but when the configuration section could contain
    also other values, not useful for this object.

    Update 'default' dictionary from 'new', never adding new keys in 'default',
    but updating just the values of existing ones.

    Moreover, convert the types of the new dict from string.

    >>> default =  {'default 1': 0,    'default 2': 'hello!'}
    >>> new     =  {'default 1': '1234', 'unknown': 'who cares'}
    >>> selective_update(default, new)
    >>> default == {'default 1': 1234, 'default 2': 'hello!'}
    True

    When 'check_type' is True, use the default dictionary as a template to
    convert the type of new dictionary values, instead of using automatic
    conversion. Raise a ValueError if a new value is not compliant with the
    default type.

    >>> default =  {'default 1': 0,         'default 2': 'hello!'}
    >>> new     =  {'default 1': '0.0.0.0', 'unknown': 'who cares'}
    >>> selective_update(default, new, check_type=True)
    [ValueError("invalid literal for int() with base 10: '0.0.0.0'",)]
    >>> default == {'default 1': 0,         'default 2': 'hello!'}
    True
    '''
    if not new: return
    keys = set(default.keys()) & set(new.keys())
    failures = []
    for k in keys:
        try:
            if check_type: value = type(default[k])(new[k]) # could raise ValueError
            else:          value = autoconvert_type(new[k])
            default[k] = value
        except ValueError as e:
            failures.append(e)
    if failures: return failures
        
def filter_dict(options, regexp):
    '''
    Useful to handle groups of sections or options. Select keys from a
    dictionary and remove the common part from their names.

    >>> o = {
    ...  'core'         : {'cron': ''},
    ...  'component test 1'  : {'option': 'value'},
    ...  'new type'     : {},
    ...  'component test two': {'option': 'value'},
    ... }
    >>> filter_dict(o,  'component (.*)') == {
    ...  'test 1'   : {'option': 'value'},
    ...  'test two' : {'option': 'value'},
    ... }
    True
    '''
    filtered = {}
    for section, options in options.items():
        match = re.search(regexp, section)
        if match:
            filtered[match.group(1)] = options
    return filtered
