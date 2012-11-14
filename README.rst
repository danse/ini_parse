This is just an utility module in order to ease the parsing of ini files and
the type conversion for python 2.x. In python 3 the standard library modules
are better, and a module like that would probably be less useful.  I'm using
this to parse .ini files within a complex infrastructure component, with many
configuration variables and sections.

This module helps for:

 - Automatic type conversion

 - Section templating

 - Easy definition of default values for options

 - Providing dictionary-like option groups (called "multioptions")

As a general approach, I choosed to not use custom objects but just builtin
types like dictionaries as output and input of methods, to keep things simple.
I think that simple objects and methods may define usage patterns which are
encapsulated into functions like 'selective_update'

Multioptions
____________

This kind of options deserves a specific coverage, since it may result complex
for those writing the configuration files.

The purpose of this feature is to write a mapping, like a dictionary, in a
configuration file. If a component needs a structure like the following to be
configurable::

 d = {
    'level one' : {
        'key one' : 'value one',
        'key two' : 'value two',
        }
    'level two' : {
        'key three' : 'value three',
        }
    }

How to write it in a configuration file? With ini_parse, it may look flattened
like::

 level_one_key_one   = value one
 level_one_key_two   = value two
 level_two_key_three = value three

Which is not so good-looking, but it allows you to insert a very complex
configurable structure in your configuration file.

Templating
__________

This functionality allows you to simplify multiple sections with share some
common values.

If you write something like::

 [template a]
 b = b
 c = c
 d = d
 i = i

 [section e]
 template = a

 [section f]
 template = a

 [section g]
 template = a
 c = h

With ini_parse that will be equivalent to writing::

 [section e]
 b = b
 c = c
 d = d
 i = i

 [section f]
 b = b
 c = c
 d = d
 i = i

 [section g]
 b = b
 c = h
 d = d
 i = i

So the file will be simplyfied with templates, and the common values between
sections will be more evident.
