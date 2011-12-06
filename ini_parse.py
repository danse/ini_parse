'''
Utilities for handling option values and sections. I choosed to not use custom
objects but just standard dictionaries to keep things simple. Nonetheless, they
are used with common patterns which are encapsulated into functions like
'selective_update'
'''

import re
from cStringIO import StringIO
import ConfigParser
import logging
from pprint import pprint

def ini_to_dict(ini):
    '''
    >>> ini = """
    ... [core]
    ... log = value
    ... main_loop_timeout = 5.9
    ...
    ... [other section]
    ... other variable = value
    ... """
    >>> ini_to_dict(ini) == \
    {'core': {'log': 'value', 'main_loop_timeout': '5.9'}, 'other section': {'other variable': 'value'}}
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
    Duplicate the whole 'node 1' section changing just the host

    >>> providers = {
    ...  'a template': {'host': '111.111.111.111',
    ...                 'port': '1234',
    ...                 'configure': 'a',
    ...  }
    ... }
    >>> users = {
    ...  'user one': {'extra': 'value', 'template': 'a template'},
    ...  'user two': {'other': 'value', 'host': '222.222.222.222', 'template': 'a template'},
    ... }
    >>> apply_templates(providers, users) == {
    ... 'user one': {'configure': 'a',
    ...             'extra': 'value',
    ...             'host': '111.111.111.111',
    ...             'port': '1234'},
    ... 'user two': {'configure': 'a',
    ...             'host': '222.222.222.222',
    ...             'other': 'value',
    ...             'port': '1234'}}
    True
    >>> r = apply_templates({}, users)
    Traceback (most recent call last):
       ...
    Exception: Option "template = a template" defined in section "user one", but section "template a template" is missing
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
    Filter and parse options based on a prefix, in order to build a dictionary

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
    >>> parse_multioption(options, 'ini_dict__') == {'key3': 'val3', 'key2': 'val2', 'key1': 'val1'}
    True
    >>> parse_multioption(options, 'another_dict___') == {'keyB': 'valB', 'keyA': 'valA'}
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

def autoconvert_type(value):
    '''Guess the type of a value'''
    for conversion in (int, float, str):
        try: return conversion(value)
        except ValueError: pass

def selective_update(default, new=None, check_type=False):
    '''
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
    conversion. This is functionally not related with a selective update, but
    this function will be used where also a type conversion is important.

    >>> default =  {'default 1': 0,         'default 2': 'hello!'}
    >>> new     =  {'default 1': '0.0.0.0', 'unknown': 'who cares'}
    >>> selective_update(default, new, check_type=True) # doctest: +ELLIPSIS
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
    Select keys from a dictionary and remove the common part from their names

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
