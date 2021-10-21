
import os
import tkinter
import unittest

from minarca_client.core.compat import IS_LINUX, IS_MAC, IS_WINDOWS
from minarca_client.ui import tkvue

NO_DISPLAY = not os.environ.get('DISPLAY', False)


class DataTest(unittest.TestCase):

    def setUp(self):
        self.last_value = None
        return super().setUp()

    def callback(self, value):
        self.last_value = value

    def test_get_set_variable(self):
        data = tkvue.Context({'var1': 'foo'})
        data.var1 = 'bar'
        self.assertEqual(data.var1, 'bar')
        data.set('var1', 'rat')
        self.assertEqual(data.var1, 'rat')

    def test_get_computed(self):
        data = tkvue.Context({
            'var1': 1,
            'var2': 2,
            'sum': tkvue.computed(lambda store: store.var1 + store.var2)
        })
        self.assertEqual(data.sum, 3)

    def test_watch_with_variable(self):
        data = tkvue.Context({'var1': 'foo'})
        data.watch('var1', self.callback)
        data.var1 = 'bar'
        self.assertEqual(self.last_value, 'bar')

    def test_watch_with_computed(self):
        data = tkvue.Context({
            'var1': 1,
            'var2': 2,
            'sum': tkvue.computed(lambda store: store.var1 + store.var2)
        })
        data.watch('sum', self.callback)
        data.var1 = 4
        self.assertEqual(self.last_value, 6)

    def test_watch_list(self):
        data = tkvue.Context(
            {'var1': [1, 2, 3, 4]},
        )
        data.watch('var1', self.callback)
        data.var1 = [1, 2, 3]
        self.assertEqual(self.last_value, [1, 2, 3])

    def test_unwatch(self):
        data = tkvue.Context(
            {'var1': 'foo'},
        )
        data.watch('var1', self.callback)
        data.var1 = 'bar'
        self.assertEqual(self.last_value, 'bar')
        data.unwatch('var1', self.callback)
        data.var1 = 'foo'
        self.assertEqual(self.last_value, 'bar')

    def test_eval(self):
        data = tkvue.Context(
            {'var1': [1, 2, 3, 4]},
        )
        self.assertEqual(2, data.eval('var1[1]'))

    def test_watch_list_item(self):
        data = tkvue.Context(
            {'var1': [1, 2, 3, 4]},
        )
        data.watch('var1[1]', self.callback)
        data.var1 = [1, 2, 3]
        self.assertEqual(self.last_value, 2)

    def test_new_child(self):
        data = tkvue.Context(
            {'var1': [1, 2, 3, 4]},
        )
        data2 = data.new_child(item=tkvue.computed(lambda self: self.var1[3]))
        # Item doesn't exists in data
        with self.assertRaises(KeyError):
            data.item
        # Item is equals to var[3] in data2
        self.assertEqual(data2.item, 4)
        # Call to function also work.
        data2.eval('callback(item)', callback=self.callback)
        self.assertEqual(self.last_value, 4)

    def test_new_child_watch(self):
        # Given a parent context with a list
        data = tkvue.Context(
            {'var1': [1, 2, 3, 4]},
        )
        # Given a child context with computed value on parent
        child = data.new_child(item=tkvue.computed(lambda self: self.var1[1]))
        self.assertEqual(child.item, 2)
        # Given a watcher on computed value
        child.watch('item', self.callback)
        # When updating the parent
        data.var1 = [2, 3, 4]
        # Then the watcher get called.
        self.assertEqual(self.last_value, 3)

    def test_new_child_unwatch(self):
        # Given a parent context
        data = tkvue.Context(
            {'var1': 'foo'},
        )
        # Given a child context with computed value on parent
        child = data.new_child(item=tkvue.computed(lambda self: self.var1 + 'bar'))
        self.assertEqual(child.item, 'foobar')
        # Given a watcher on computed value
        child.watch('item', self.callback)
        data.var1 = 'bar'
        self.assertEqual(self.last_value, 'barbar')
        # When removing watcher
        child.unwatch('item', self.callback)
        # Then updating the parent doesn't notify anymore
        data.var1 = 'rat'
        self.assertEqual(self.last_value, 'barbar')

    def test_setter_child(self):
        # Given a parent context
        data = tkvue.Context(
            {'var1': 'foo'},
        )
        # Given a child context
        child = data.new_child()
        # When setting a value on the child context.
        child.var1 = 'bar'
        # Then the value is update into the parent context.
        self.assertEqual(data.var1, 'bar')

    def test_computed_dependencies_updated(self):
        # Given a parent context
        data = tkvue.Context(
            {'var1': True, 'var2': True},
        )
        # Given a watching on both variables.
        data.watch('var1 or var2', self.callback)
        # When setting a value on the child context.
        data.var1 = False
        data.var2 = False
        # Then the value is update into the parent context.
        self.assertEqual(self.last_value, False)


class Dialog(tkvue.Component):
    template = """
    <Tk>
        <Frame pack-fill="x" pack-expand="1">
            <!-- Single and dual binding -->
            <Entry id="entry" textvariable="{{text_value}}" />
            <label id="label" text="{{text_value}}" />
        </Frame>
        <Frame pack-fill="x" pack-expand="1">
            <Button id="button" visible="{{button_visible}}" text="Visible" />
        </Frame>
        <Frame id="people" pack-fill="x" pack-expand="1">
            <Label for="i in names" text="{{i}}" />
        </Frame>
        <Frame pack-fill="x" pack-expand="1">
            <Radiobutton id="blue" variable="{{selected_color}}" value="blue" text="blue"/>
            <Radiobutton id="red" variable="{{selected_color}}" value="red" text="red"/>
            <Radiobutton id="green" variable="{{selected_color}}" value="green" text="green"/>
            <Combobox id="combo" textvariable="{{selected_color}}" values="blue red green" />
        </Frame>
        <Frame pack-fill="x" pack-expand="1">
            <Checkbutton id="checkbutton" text="foo" selected="{{checkbutton_selected}}" command="checkbutton_invoke"/>
        </Frame>
    </Tk>
    """

    def __init__(self, master=None):
        self.data = tkvue.Context({
            'text_value': 'foo',
            'button_visible': True,
            'names': ['patrik', 'annik', 'michel', 'denise'],
            'selected_color': 'blue',
            'checkbutton_selected': True,
        })
        super().__init__(master=master)

    def checkbutton_invoke(self):
        self.data.checkbutton_selected = not self.data.checkbutton_selected


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class ComponentTest(unittest.TestCase):

    def setUp(self):
        self.dlg = Dialog()
        super().setUp()

    def tearDown(self):
        self.dlg.destroy()
        self.pump_events()
        super().tearDown()

    def pump_events(self):
        while self.dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

    def test_open_close(self):
        self.pump_events()

    def test_simple_binding(self):
        # Given a dialog with a simple binding
        self.pump_events()
        self.assertEqual('foo', self.dlg.label.cget('text'))
        # When updating the value of the context
        self.dlg.data.text_value = 'bar'
        # Then thw widget get updated
        self.assertEqual('bar', self.dlg.label.cget('text'))

    @unittest.skipIf(IS_WINDOWS, 'fail to reliably force focus on windows')
    def test_dual_binding(self):
        # Given a dialog with a simple binding
        self.dlg.root.lift()
        self.pump_events()
        self.assertEqual('foo', self.dlg.label.cget('text'))
        self.assertEqual('foo', self.dlg.entry.getvar(self.dlg.entry.cget('text')))
        # Given the root windows has focus.
        self.dlg.root.focus_force()
        self.pump_events()
        self.assertEqual(self.dlg.root.focus_get(), self.dlg.root)
        # When typing into the entry field
        self.dlg.entry.focus_set()
        self.dlg.entry.event_generate('<i>')
        self.pump_events()
        # Then the store get updated
        self.assertEqual('ifoo', self.dlg.data.text_value)
        self.assertEqual('ifoo', self.dlg.label.cget('text'))
        self.assertEqual('ifoo', self.dlg.entry.getvar(self.dlg.entry.cget('text')))

    @unittest.skipIf(IS_WINDOWS, 'fail to reliably make this test work in CICD')
    def test_visible(self):
        # Given a dialog with a simple binding
        self.pump_events()
        self.assertTrue(self.dlg.button.winfo_ismapped())
        # When typing into the entry field
        self.dlg.data.button_visible = False
        self.pump_events()
        # Then the store get updated
        self.assertFalse(self.dlg.button.winfo_ismapped())

    def test_for_loop(self):
        # Given a dialog with a for loop
        self.pump_events()
        self.assertEqual(4, len(self.dlg.people.winfo_children()))
        # When Adding element to the list
        self.dlg.data.names = ['patrik', 'annik']
        self.pump_events()
        # Then the dialog get updated
        self.assertEqual(2, len(self.dlg.people.winfo_children()))

    def test_dual_binding_combo_and_radio(self):
        # Given a dialog with a for loop
        self.pump_events()
        # When selecting an item with radio
        self.dlg.red.invoke()
        self.pump_events()
        # Then radio button get updated
        self.assertEqual('red', self.dlg.data.selected_color)

    @unittest.skipIf(IS_MAC, 'this fail on MacOS when running in test suite')
    def test_checkbutton_selected(self):
        # Given a dialog with checkbutton binded with `selected` attribute
        self.pump_events()
        self.assertEqual(self.dlg.checkbutton.state(), ('selected',))
        # When updating checkbutton_selected value
        self.dlg.data.checkbutton_selected = False
        self.pump_events()
        # Then the widget get updated
        self.assertEqual(self.dlg.checkbutton.state(), tuple())

    @unittest.skipIf(IS_MAC, 'this fail on MacOS when running in test suite')
    def test_checkbutton_selected_command(self):
        # Given a dialog with checkbutton binded with `selected` attribute
        self.pump_events()
        self.assertEqual(self.dlg.checkbutton.state(), ('selected',))
        # When cliking on checkbutton
        self.dlg.checkbutton.focus_set()
        self.dlg.checkbutton.invoke()
        self.dlg.root.focus_set()
        self.pump_events()
        # Then the widget status get toggled.
        self.assertEqual(self.dlg.data.checkbutton_selected, False)
        self.assertEqual(self.dlg.checkbutton.state(), tuple())
        # When cliking on checkbutton again
        self.dlg.checkbutton.focus_set()
        self.dlg.checkbutton.invoke()
        self.dlg.root.focus_set()
        self.pump_events()
        # Then the widget status get toggled.
        self.assertEqual(self.dlg.data.checkbutton_selected, True)
        self.assertEqual(self.dlg.checkbutton.state(), ('selected',))
