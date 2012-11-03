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
