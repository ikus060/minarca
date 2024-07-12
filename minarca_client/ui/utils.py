from kivy.properties import AliasProperty


def alias_property(setter=None, bind=[], cache=False, rebind=False, watch_before_use=True):
    """
    Alias property decorator.
    """

    def decorator(getter):
        return AliasProperty(getter, setter, bind=bind, cache=cache, rebind=rebind, watch_before_use=watch_before_use)

    return decorator
