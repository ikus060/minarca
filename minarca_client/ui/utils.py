import functools

from kivy.properties import AliasProperty


def alias_property(bind=[]):
    """
    Alias property decorator.
    """
    return functools.partial(AliasProperty, setter=None, bind=bind)
