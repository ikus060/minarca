
# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import collections
import logging
import os
import tkinter
from html.parser import HTMLParser
from itertools import chain
from tkinter import PhotoImage, ttk

from minarca_client.locale import gettext

logger = logging.getLogger(__name__)


_components = {}  # component registry.

_default_basename = None
_default_classname = 'Tkvue'
_default_screenname = None
_default_theme = 'clam'
_default_theme_source = None


def configure_tk(basename=None, classname='Tk', screenname=None, icon=None, theme='clam', theme_source=None):
    """
    Use to configure default instance of Tkinter created by tkvue.
    """
    assert theme_source is None or os.path.isfile(theme_source)

    # Disable Tkinter default root creation
    tkinter.NoDefaultRoot()
    global _default_basename, _default_classname, _default_screenname, _default_icon, _default_theme, _default_theme_source
    _default_basename = basename
    _default_classname = classname
    _default_screenname = screenname
    _default_icon = icon
    _default_theme = theme
    _default_theme_source = theme_source


def create_toplevel(master=None):
    """
    Used to create a TopLevel window.
    """

    global _default_basename, _default_classname, _default_screenname, _default_icon, _default_theme, _default_theme_source
    if master == None:
        root = tkinter.Tk(baseName=_default_basename, className=_default_classname, screenName=_default_screenname)
        root.report_callback_exception = lambda exc, val, tb: logger.exception('Exception in Tkinter callback')
        if _default_theme_source:
            root.call('source', _default_theme_source)
        if _default_theme:
            root.call("ttk::setTheme", _default_theme)
        if _default_icon:
            root.iconphoto(True, _default_icon)
    else:
        root = tkinter.Toplevel(master)

    def _update_bg(event):
        # Skip update if event is not related to TopLevel widget.
        if root != event.widget:
            return
        # Update TopLevel background according to TTK Style.
        bg = ttk.Style(master=root).lookup('TFrame', 'background')
        root.configure(bg=bg)

    root.bind('<<ThemeChanged>>', _update_bg)

    return root


def computed(func):
    """
    Create computed attributes.
    """
    assert callable(func)
    func.__computed__ = True
    return func


def extract_tkvue(fileobj, keywords, comment_tags, options):
    """Extract messages from .html files.

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    encoding = options.pop('encoding', 'utf-8')

    class ExtractorParser(HTMLParser):

        def __init__(self):
            self.messages = []
            super().__init__()

        def handle_starttag(self, tag, attrs):
            for name, value in attrs:
                if name in ['text', 'title'] and not value.startswith('{{'):
                    self.messages.append((self.lineno, 'gettext', value, []))

    extractor = ExtractorParser()
    extractor.feed(fileobj.read().decode(encoding))
    for entry in extractor.messages:
        yield entry


class Context(collections.abc.MutableMapping):

    def __init__(self, initial_data={}, parent=None):
        'Create a new root context'
        for key, value in initial_data.items():
            assert hasattr(value, '__hash__'), "unhashable type '%s' for key %s" % (type(value), key)
        self._map = initial_data.copy()
        self._parent = parent
        self._maps = [self._map]
        self._track = None
        self._watchers = {}
        if self._parent is not None:
            self._maps += self._parent._maps

    def new_child(self, **kwargs):
        'Make a child context, inheriting enable_nonlocal unless specified'
        return self.__class__(kwargs, parent=self)

    @property
    def root(self):
        'Return root context (highest level ancestor)'
        return self if self._parent is None else self._parent.root

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self[key] = value

    set = __setattr__

    def __getitem__(self, key):
        for m in self._maps:
            if key in m:
                break
        value = m[key]
        if hasattr(value, '__computed__'):
            return value(self)
        else:
            if self._track is not None:
                self._track.append(key)
            return value

    def __setitem__(self, key, value):
        assert hasattr(value, '__hash__'), "unhashable type '%s' for key %s" % (type(value), key)
        # Dispatch setter to parent context
        if key not in self._map and self._parent:
            self._parent.__setitem__(key, value)
            return
        # Get previous value for comparaison
        prev_value = self._map[key]
        # Raise an error if the key is a computed value. Those cannot be updated.
        if hasattr(prev_value, '__computed__'):
            raise ValueError('cannot set computed attribute')
        # Save the new value.
        self._map[key] = value
        # If value changed, notify
        if prev_value != value:
            self._notify(key, value)

    def __delitem__(self, key):
        del self._map[key]

    def __len__(self):
        return sum(map(len, self._maps))

    def __iter__(self, chain_from_iterable=chain.from_iterable):
        return chain_from_iterable(self._maps)

    def __contains__(self, key, any=any):
        return any(key in m for m in self._maps)

    def __repr__(self, repr=repr):
        return ' -> '.join(map(repr, self._maps))

    def _notify(self, key, new):
        # Notify watchers.
        items = list(self._watchers.items())
        for (expr, func), (dependencies, context) in items:
            # Check if dependencies matches our key
            # Also check if the watcher is still in the list since
            # the list may get updated during notification.
            if key in dependencies and (expr, func) in self._watchers:
                func(context.watch(expr, func))

    def eval(self, expr, **kwargs):
        """
        Evaluate the given expression.
        """
        if kwargs:
            return self.new_child(**kwargs).eval(expr)
        else:
            try:
                return eval(expr, None, self)
            except Exception as e:
                raise Exception('exception occured while evaluating expression `%s`' % expr) from e

    def watch(self, expr, func):
        """
        Adding watcher on the given expression.
        """
        assert expr
        assert func and hasattr(func, '__call__')
        if expr in self._map and not hasattr(self._map[expr], '__computed__'):
            dependencies = set([expr])
            v = self.get(expr)
        else:
            self._track = []
            v = self.eval(expr)
            dependencies = set(self._track)
            self._track = None
        # Register watchers on appropriate context depending where variable is declared
        context = self
        while context:
            dep = [d for d in dependencies if d in context._map]
            if dep:
                context._watchers[(expr, func)] = (dep, self)
            context = context._parent
        return v

    def unwatch(self, expr, func):
        """
        Removing associated watchers.
        """
        context = self
        while context:
            if (expr, func) in context._watchers:
                del context._watchers[(expr, func)]
            context = context._parent

    def __bool__(self):
        return True


def _configure_image(widget, image_path):
    """
    Configure the image attribute of a Label or a Button.

    Support animated gif image.
    """

    def _next_frame():
        widget.frame = (widget.frame + 1) % len(widget.frames)
        if widget.winfo_ismapped():
            widget.configure(image=widget.frames[widget.frame])
        # Register next animation.
        widget.event_id = widget.after(150, _next_frame)

    # Check if image_path is the same.
    if getattr(widget, 'image_path', None) == image_path:
        return
    # Create a new image
    if image_path.endswith('.gif'):
        widget.frames = []
        while True:
            try:
                image = tkinter.PhotoImage(master=widget, file=image_path, format='gif -index %i' % len(widget.frames))
                widget.frames.append(image)
            except tkinter.TclError:
                # An error is raised when the index is out of range.
                break
    elif image_path in widget.image_names():
        widget.frames = [image_path]
    elif f'{image_path}_00' in widget.image_names():
        widget.frames = sorted([name for name in widget.image_names() if name.startswith(f'{image_path}_')])
    else:
        widget.frames = [tkinter.PhotoImage(master=widget, file=image_path)]
    # Update widget image with first frame.
    widget.frame = 0
    widget.configure(image=widget.frames[0])
    # Register animation.
    if len(widget.frames) > 1:
        widget.event_id = widget.after(100, _next_frame)
    elif getattr(widget, 'event_id', None):
        widget.root.after_cancel(widget.event_id)


def _configure_selected(widget, value):
    widget.state(['selected' if value else '!selected', '!alternate'])


def _configure_wrap(widget, wrap):
    # Support Text wrapping
    if wrap.lower() in ['true', '1']:
        widget.bind('<Configure>', lambda e: widget.config(wraplen=widget.winfo_width()), add='+')


class ToolTip(ttk.Frame):
    """
    Tooltip widget.
    """

    def __init__(self, master, text='', timeout=400, **kwargs):
        assert master, 'ToolTip widget required a master widget'
        assert timeout >= 0, 'timeout should be greater or equals zero (0): %s' % timeout
        super().__init__(master, **kwargs)
        self.widget = master
        self.text = text
        # Initialize internal variables
        self.tipwindow = None  # tooltip window.
        self.id = None  # event id
        self.x = self.y = 0
        self.timeout = timeout  # time in milliseconds before tooltip get displayed
        # Bind events to master
        self.master.bind('<Enter>', self.enter)
        self.master.bind('<Leave>', self.leave)
        self.master.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.x = event.x
        self.y = event.y
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.master.after(self.timeout, self.showtip)

    def unschedule(self):
        if self.id:
            self.master.after_cancel(self.id)
        self.id = None

    def showtip(self):
        if self.tipwindow:
            return
        x = self.master.winfo_rootx() + self.x
        y = self.master.winfo_rooty() + self.y
        self.tipwindow = tkinter.Toplevel(self.master)
        try:
            self.tipwindow.wm_overrideredirect(True)
            # if not sys.platform.startswith('darwin'):
            # if running_mac() and ENABLE_MAC_NOTITLEBAR_PATCH:
            # self.tipwindow.wm_overrideredirect(False)
        except Exception as e:
            print('* Error performing wm_overrideredirect in showtip *', e)
        self.tipwindow.wm_geometry("+%d+%d" % (x, y))
        self.tipwindow.wm_attributes("-topmost", 1)
        label = ttk.Label(self.tipwindow, text=self.text, justify=tkinter.LEFT, relief=tkinter.SOLID, borderwidth=1, padding=5, style='tooltip.TLabel')
        label.pack()

    def hidetip(self):
        """
        Destroy the tooltip window
        """
        if self.tipwindow:
            self.tipwindow.destroy()
        self.tipwindow = None

    def pack(self, cfg={}, **kw):
        # Do nothing This widget must not be pack
        pass

    def configure(self, cnf={}, **kw):
        self.text = cnf.pop('text', kw.pop('text', self.text))
        # Timeout
        timeout = cnf.pop('timeout', kw.pop('timeout', self.timeout))
        assert timeout >= 0, 'timeout should be greater or equals zero (0): %s' % timeout
        self.timeout = timeout
        # Pass other config to widget.
        super().configure(cnf, **kw)

    def cget(self, key):
        if key == 'text':
            return self.text
        elif key == 'timeout':
            return self.timeout
        return super().cget(key)

    def bind(self, *args, **kwargs):
        self.widget.bind(*args, **kwargs)

    def event_generate(self, *args, **kwargs):
        self.widget.event_generate(*args, **kwargs)


class Loop():
    """
    Pseudo widget used to handle for loops.
    """

    def __init__(self, tree, for_expr, master, context, widget_factory):
        assert tree
        assert ' in ' in for_expr, 'for expression must have the for <target> in <list>'
        assert master
        assert context
        self.tree = tree.copy()
        self.tree.attrs.pop('for', 'None')
        self.master = master
        self.context = context
        self.widget_factory = widget_factory
        self.idx = 0
        self.widgets = []
        # Validate expression by evaluating it.
        self.loop_target, unused, self.loop_items = for_expr.partition(' in ')
        items = context.eval(self.loop_items)
        # Register our self
        context.watch(self.loop_items, self.update_items)
        # Children shildren
        self.update_items(items)

    def create_widget(self, idx):
        child_var = {self.loop_target: computed(lambda context: context.eval(self.loop_items)[idx])}
        child_context = self.context.new_child(**child_var)
        return self.widget_factory(master=self.master, tree=self.tree, context=child_context)

    def update_items(self, items):
        # We may need to create new widgets.
        while self.idx < len(items):
            widget = self.create_widget(self.idx)
            # Make sure to pack widget at the right location.
            # TODO Fix parent when all item get deleteds
            widget.pack(after=self.widgets[-1] if self.widgets else None)
            self.widgets.append(widget)
            self.idx += 1
        # We may need to delete widgets
        while self.idx > len(items):
            self.widgets.pop(-1).destroy()
            self.idx -= 1


class ScrolledFrame(ttk.Frame):
    """
    Let provide our own Scrolled frame.
    """

    def __init__(self, master, *args, **kw):

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        def _on_mousewheel(event):
            # Skip scroll if cvans is bigger then content.
            if canvas.yview() == (0.0, 1.0):
                return
            # Pick scroll directio dependinds of event <Button-?> or delta value <MouseWheel>
            if event.num == 5 or event.delta < 0:
                scroll = 1
            elif event.num == 4 or event.delta > 0:
                scroll = -1
            canvas.yview_scroll(scroll, "units")

        def _bind_to_mousewheel(event):
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)
            canvas.bind_all("<MouseWheel>", _on_mousewheel)  # On Windows

        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            canvas.unbind_all("<MouseWheel>")  # On Windows

        def _update_bg(event):
            bg = ttk.Style(master=master).lookup('TFrame', 'background')
            canvas.configure(bg=bg)

        ttk.Frame.__init__(self, master, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = ttk.Scrollbar(self, orient=tkinter.VERTICAL)
        vscrollbar.pack(fill=tkinter.Y, side=tkinter.RIGHT, expand=tkinter.FALSE)
        canvas = tkinter.Canvas(self, bd=0, highlightthickness=0,
                                yscrollcommand=vscrollbar.set)
        canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = ttk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tkinter.NW)

        interior.bind('<Configure>', _configure_interior)
        canvas.bind('<Configure>', _configure_canvas)
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        canvas.bind('<<ThemeChanged>>', _update_bg)


def getwidget(name):
    if name == 'scrolledframe':
        return ScrolledFrame
    elif name == 'tooltip':
        return ToolTip
    elif name == 'toplevel':
        return create_toplevel
    # lookup widget by name
    for a in dir(ttk):
        if a.lower() == name.lower():
            func = getattr(ttk, a)
            if hasattr(func, '__call__'):
                return func
    # lookup in components. default to None
    return _components.get(name, None)


class Element(object):
    """
    HTML element
    """
    __slots__ = ['tag', 'attrs', 'children', 'parent']

    def __init__(self, tag='', attrs={}, parent=None):
        assert tag
        assert isinstance(attrs, dict)
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.parent = parent
        if parent:
            self.parent.children.append(self)

    def copy(self):
        node = Element(self.tag, self.attrs.copy())
        node.children = self.children.copy()
        return node


class Parser(HTMLParser):
    """
    HTML Parser
    """

    def __init__(self):
        self.node = self.tree = None
        super().__init__()

    def handle_starttag(self, tag, attrs):
        self.node = Element(tag, dict(attrs), self.node)
        if self.tree is None:
            self.tree = self.node

    def handle_endtag(self, tag):
        assert self.node.tag == tag, 'unexpected end of tag `%s` on line %s ' % (tag, self.lineno)
        self.node = self.node.parent


class TkVue():

    def __init__(self, component, master):
        assert component
        assert hasattr(component, 'template'), 'component %s must define a template' % component.__class__.__name__

        # Keep reference to the component.
        self.component = component
        if not hasattr(self.component, 'data'):
            self.component.data = Context()

        # Read the template
        parser = Parser()
        if isinstance(component.template, bytes):
            parser.feed(component.template.decode('utf8'))
        else:
            parser.feed(component.template)

        # Generate the widget from template.
        self.component.root = self._walk(master=master, tree=parser.tree, context=self.component.data)

    def _bind_attrs(self, master, tag, attrs, context):
        """
        Resolve attributes values for the given widget.
        Then apply them using configure() and pack()
        """
        assert tag
        assert attrs is not None

        # Get widget class.
        Widget = getwidget(tag)
        assert Widget, 'cannot find widget matching tag name: ' + tag

        #
        # Command may only be define when creating widget.
        # So let process this attribute before creating the widget.
        #
        def command(value):
            assert not value.startswith('{{'), "command attributes doesn't support bindind"
            funcs = {k: getattr(self.component, k) for k in dir(self.component) if callable(getattr(self.component, k))}
            # May need to adjust this to detect expression.
            if '(' in value or '=' in value:
                def func():
                    return context.eval(value, **funcs)
            else:
                func = funcs.get(value, None)
                assert func and hasattr(func, '__call__'), 'command attribute value should define a function name'
            return func

        kwargs = {}
        if 'command' in attrs:
            kwargs['command'] = command(attrs['command'])

        #
        # Create widget.
        #
        widget = Widget(master=master, **kwargs)

        #
        # Assign widget to variables.
        #
        if 'id' in attrs:
            setattr(self.component, attrs['id'], widget)

        def bind_attr(value, func):
            if value.startswith('{{') and value.endswith('}}'):
                expr = value[2:-2]
                # Register observer
                expr_value = context.watch(expr, func)
                # Assign the value
                func(expr_value)
                # Handle disposal
                widget.bind("<Destroy>", lambda event, expr=expr, func=func: context.unwatch(expr, func), add='+')
            else:
                # Plain value with evaluation.
                func(value)

        def dual_bind_attr(value, attr):
            assert value.startswith('{{') and value.endswith('}}')
            expr = value[2:-2]
            # Get current variable type.
            # And create appropriate variable type.
            var_type = type(context.eval(expr))
            if var_type == int:
                var = tkinter.IntVar(master=widget)
            elif var_type == float:
                var = tkinter.DoubleVar(master=widget)
            elif var_type == bool:
                var = tkinter.BooleanVar(master=widget)
            else:
                var = tkinter.StringVar(master=widget)
            # Support dual-databinding
            bind_attr(v, lambda new_value, var=var: var.set(new_value))
            var.trace_add('write', lambda *args, var=var: context.set(expr, var.get()))
            # TODO trace_remove
            widget.configure({attr: var})

        # Check if args contains pack or :pack
        # If the widget doesn't need to be pack. We don't need to compute changes.
        if hasattr(widget, 'pack'):
            pack_attrs = {k[5:]: v for k, v in attrs.items() if k.startswith('pack-')}
            if 'visible' in attrs:
                bind_attr(attrs['visible'], lambda value: widget.pack(pack_attrs) if value else widget.forget())
            else:
                widget.pack(pack_attrs)
        for k, v in attrs.items():
            if k in ['id', 'command', 'visible'] or k.startswith('pack-'):
                # ignore pack attribute
                continue
            elif k in ['textvariable', 'variable']:
                dual_bind_attr(v, k)
            elif k == 'selected':
                # Special attribute for Button, Checkbutton
                bind_attr(v, lambda value: widget.state(['selected' if value else '!selected', '!alternate']))
            elif k in ['text']:
                bind_attr(v, lambda value, k=k: widget.configure(**{k: gettext(value)}))
            elif k == 'wrap':
                bind_attr(v, lambda value: _configure_wrap(widget, value))
            elif k == 'image':
                bind_attr(v, lambda value: _configure_image(widget, value))
            elif k == 'geometry':
                # Defined on TopLevel
                func = getattr(widget, k, None)
                assert func, f'{k} is not a function of widget'
                func(v)
            elif k == 'title':
                # Defined on TopLevel
                func = getattr(widget, k, None)
                assert func, f'{k} is not a function of widget'
                func(gettext(v))
            else:
                bind_attr(v, lambda value, k=k: widget.configure(**{k: value}))

        return widget

    def _create_command(self, value, context):
        """
        Command may only be define when creating widget.
        So let process this attribute before creating the widget.
        """
        assert not value.startswith('{{'), "command attributes doesn't support bindind"
        funcs = {k: getattr(self.component, k) for k in dir(self.component) if callable(getattr(self.component, k))}
        # May need to adjust this to detect expression.
        if '(' in value or '=' in value:
            def func():
                return context.eval(value, **funcs)
        else:
            func = funcs.get(value, None)
            assert func and hasattr(func, '__call__'), 'command attribute value should define a function name'
        return func

    # TODO Make this function static.
    def _walk(self, master, tree, context):
        assert tree
        assert context
        # Create widget to represent the node.
        attrs = tree.attrs
        # Handle for loop
        if 'for' in attrs:
            widget = Loop(tree, attrs['for'], master=master, context=context, widget_factory=self._walk)
            tree.children = []
            return None
        try:
            # Create the widget with required attributes.
            widget = self._bind_attrs(master, tree.tag, attrs, context)
        except Exception as e:
            raise Exception(str(e) + ' for tag <%s %s>' % (tree.tag, ' '.join(['%s="%s"' % (k, v) for k, v in tree.attrs.items()])))
        # Support ScrolledFrame with `interior`
        interior = getattr(widget, 'interior', widget)
        # Create child widgets.
        for child in tree.children:
            self._walk(master=interior, tree=child, context=context)
        return widget


class Component():
    template = """<Label text="default template" />"""

    def __init_subclass__(cls, **kwargs):
        if cls not in _components:
            _components[cls.__name__.lower()] = cls
        super().__init_subclass__(**kwargs)

    def __init__(self, master=None):
        self.root = None
        self.vue = TkVue(self, master=master)

    def __getattr__(self, name):
        return getattr(self.root, name)
