import sublime
import sublime_plugin

from Vintageous import plugins
from Vintageous.vi import inputs
from Vintageous.vi import utils
from Vintageous.vi.cmd_defs import ViOperatorDef
from Vintageous.vi.core import ViTextCommandBase
from Vintageous.vi.inputs import input_types
from Vintageous.vi.inputs import parser_def
from Vintageous.vi.search import reverse_search
from Vintageous.vi.utils import modes
from Vintageous.vi.utils import regions_transformer

import re


@plugins.register(keys=[('ys', (modes.NORMAL, modes.OPERATOR_PENDING))])
class ViSurround(ViOperatorDef):
    def __init__(self, *args, **kwargs):
        ViOperatorDef.__init__(self, *args, **kwargs)

        self.scroll_into_view = True
        self.updates_xpos = True
        self.repeatable = True
        self.motion_required = True

        self.input_parser = parser_def(
                            command=inputs.one_char,
                            interactive_command=None,
                            input_param=None,
                            on_done=None,
                            type=input_types.AFTER_MOTION)

    @property
    def accept_input(self):
        single = len(self.inp) == 1 and self.inp != '<'
        tag = re.match('<.*?>', self.inp)
        return not(single or tag)

    def accept(self, key):
        self._inp += utils.translate_char(key)
        return True

    def translate(self, state):
        cmd = {}
        cmd['action'] = '_vi_plug_y_s'
        cmd['action_args'] = {'mode': state.mode,
                              'surround_with': self.inp}
        return cmd


# def validate_vi_plug_y_s(in_):
#     single = len(in_) == 1 and in_ != '<'
#     tag = re.match('<.*?>', in_)
#     return single or tag


# def validate_vi_plug_c_s(in_):
#     return len(in_) == 2


# def validate_vi_plug_d_s(in_):
#     return len(in_) == 1


# def do_post_load():
#     from Vintageous.state import plugin_manager

#     # register action for action parsing
#     @plugin_manager.register_action
#     def vi_plug_y_s(vi_cmd_data):
#         vi_cmd_data['action']['command'] = '_vi_plug_y_s'
#         vi_cmd_data['action']['args'] = {'mode': vi_cmd_data['mode'], 'surround_with': vi_cmd_data['user_action_input']}
#         vi_cmd_data['follow_up_mode'] = 'vi_enter_normal_mode'

#         return vi_cmd_data


#     @plugin_manager.register_action
#     def vi_plug_c_s(vi_cmd_data):
#         vi_cmd_data['motion_required'] = False
#         vi_cmd_data['action']['command'] = '_vi_plug_c_s'
#         vi_cmd_data['action']['args'] = {'mode': vi_cmd_data['mode'], 'replace_what': vi_cmd_data['user_action_input']}
#         vi_cmd_data['motion']['command'] = '_vi_no_op'
#         vi_cmd_data['motion']['args'] = {}
#         vi_cmd_data['follow_up_mode'] = 'vi_enter_normal_mode'

#         return vi_cmd_data


#     @plugin_manager.register_action
#     def vi_plug_d_s(vi_cmd_data):
#         vi_cmd_data['motion_required'] = False
#         vi_cmd_data['action']['command'] = '_vi_plug_d_s'
#         vi_cmd_data['action']['args'] = {'mode': vi_cmd_data['mode'], 'replace_what': vi_cmd_data['user_action_input']}
#         vi_cmd_data['motion']['command'] = '_vi_no_op'
#         vi_cmd_data['motion']['args'] = {}
#         vi_cmd_data['follow_up_mode'] = 'vi_enter_normal_mode'

#         return vi_cmd_data


#     plugin_manager.register_composite_command({('vi_y', 'vi_s'): ('vi_plug_y_s', DIGRAPH_ACTION)})
#     plugin_manager.register_action_input_parser({'vi_plug_y_s': (INPUT_AFTER_MOTION, validate_vi_plug_y_s)})

#     plugin_manager.register_composite_command({('vi_c', 'vi_s'): ('vi_plug_c_s', DIGRAPH_ACTION)})
#     plugin_manager.register_action_input_parser({'vi_plug_c_s': (INPUT_IMMEDIATE, validate_vi_plug_c_s)})

#     plugin_manager.register_composite_command({('vi_d', 'vi_s'): ('vi_plug_d_s', DIGRAPH_ACTION)})
#     plugin_manager.register_action_input_parser({'vi_plug_d_s': (INPUT_IMMEDIATE, validate_vi_plug_d_s)})

# add key bindings in .sublime-keymap file
# (none in this case: ys<arg>; y and s are standard Vim commands defined in Vintageous)

# actual command implementation
class _vi_plug_y_s(ViTextCommandBase):
    PAIRS = {
        '(': ('(', ')'),
        ')': ('( ', ' )'),
        '[': ('[', ']'),
        ']': ('[ ', ' ]'),
        '{': ('{', '}'),
        '}': ('{ ', ' }'),
    }
    def run(self, edit, mode=None, surround_with='"', count=1, motion=None):
        def f(view, s):
            if mode == modes.INTERNAL_NORMAL:
                self.surround(edit, s, surround_with)
                return sublime.Region(s.begin())
            return s

        if not motion:
            self.enter_normal_mode(mode)
            raise ValueError('motion required')

        self.view.run_command(motion['motion'], motion['motion_args'])

        if surround_with:
            regions_transformer(self.view, f)

        self.enter_normal_mode(mode)

    def surround(self, edit, s, surround_with):
        open_, close_ = _vi_plug_y_s.PAIRS.get(surround_with, (surround_with, surround_with))

        # Takes <q class="foo"> and produces: <q class="foo">text</q>
        if open_.startswith('<'):
            name = open_[1:].strip()[:-1].strip()
            name = name.split(' ', 1)[0]
            self.view.insert(edit, s.b, "</{0}>".format(name))
            self.view.insert(edit, s.a, surround_with)
            return

        self.view.insert(edit, s.b, close_)
        self.view.insert(edit, s.a, open_)


class _vi_plug_c_s(sublime_plugin.TextCommand):
    PAIRS = {
        '(': ('(', ')'),
        ')': ('( ', ' )'),
        '[': ('[', ']'),
        ']': ('[ ', ' ]'),
        '{': ('{', '}'),
        '}': ('{ ', ' }'),
    }
    def run(self, edit, mode=None, replace_what=''):
        def f(view, s):
            if mode == _MODE_INTERNAL_NORMAL:
                self.replace(edit, s, replace_what)
                return s
            return s

        if replace_what:
            regions_transformer(self.view, f)

    def replace(self, edit, s, replace_what):
        old, new = tuple(replace_what)
        open_, close_ = _vi_plug_c_s.PAIRS.get(old, (old, old))
        new_open, new_close = _vi_plug_c_s.PAIRS.get(new, (new, new))

        if len(open_) == 1 and open_ == 't':
            open_, close_ = ('<.*?>', '</.*?>')
            next_ = self.view.find(close_, s.b)
            prev_ = reverse_search(self.view, open_, end=s.b, start=0)
        else:
            # brute force
            next_ = self.view.find(close_, s.b, sublime.LITERAL)
            prev_ = reverse_search(self.view, open_, end=s.b, start=0, flags=sublime.LITERAL)

        if not (next_ and prev_):
            return

        self.view.replace(edit, next_, new_close)
        self.view.replace(edit, prev_, new_open)


class _vi_plug_d_s(sublime_plugin.TextCommand):
    PAIRS = {
        '(': ('(', ')'),
        ')': ('( ', ' )'),
        '[': ('[', ']'),
        ']': ('[ ', ' ]'),
        '{': ('{', '}'),
        '}': ('{ ', ' }'),
    }
    def run(self, edit, mode=None, replace_what=''):
        def f(view, s):
            if mode == _MODE_INTERNAL_NORMAL:
                self.replace(edit, s, replace_what)
                return s
            return s

        if replace_what:
            regions_transformer(self.view, f)

    def replace(self, edit, s, replace_what):
        old, new = (replace_what, '')
        open_, close_ = _vi_plug_c_s.PAIRS.get(old, (old, old))

        if len(open_) == 1 and open_ == 't':
            open_, close_ = ('<.*?>', '</.*?>')
            next_ = self.view.find(close_, s.b)
            prev_ = reverse_search(self.view, open_, end=s.b, start=0)
        else:
            # brute force
            next_ = self.view.find(close_, s.b, sublime.LITERAL)
            prev_ = reverse_search(self.view, open_, end=s.b, start=0, flags=sublime.LITERAL)

        if not (next_ and prev_):
            return

        self.view.replace(edit, next_, new)
        self.view.replace(edit, prev_, new)
