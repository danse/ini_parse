This is a bounch of useful logic for handling option values and sections from
an .ini file within a complex application, with many configuration variables
and sections.

As a general approach, I choosed to not use custom objects but just builtin
types like dictionaries as output and input of methods, to keep things simple.
I think that simple objects and methods may define usage patterns which are
encapsulated into functions like 'selective_update'
