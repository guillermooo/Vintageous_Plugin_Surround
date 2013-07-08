import sublime
import sublime_plugin

from Vintageous.vi.constants import regions_transformer
from Vintageous.vi.constants import _MODE_INTERNAL_NORMAL
from Vintageous.vi.constants import MODE_VISUAL
from Vintageous.vi.constants import DIGRAPH_ACTION
from Vintageous.vi.constants import INPUT_AFTER_MOTION

import re


plugin_manager = None

def plugin_loaded():
    sublime.set_timeout(do_post_load, 75)


def validate_vi_plug_s_y(in_):
    single = len(in_) == 1 and in_ != '<'
    tag = re.match('<.*?>', in_)
    return single or tag


def do_post_load():
    global plugin_manager
    from Vintageous.state import plugin_manager as pm
    plugin_manager = pm

    # register action for action parsing
    @plugin_manager.register_action
    def vi_plug_s_y(vi_cmd_data):
        vi_cmd_data['action']['command'] = '_vi_plug_y_s'
        vi_cmd_data['action']['args'] = {'mode': vi_cmd_data['mode'], 'surround_with': vi_cmd_data['user_action_input']}
        vi_cmd_data['follow_up_mode'] = 'vi_enter_normal_mode'

        return vi_cmd_data


    plugin_manager.register_composite_command({('vi_y', 'vi_s'): ('vi_plug_s_y', DIGRAPH_ACTION)})
    plugin_manager.register_action_input_parser({'vi_plug_s_y': (INPUT_AFTER_MOTION, validate_vi_plug_s_y)})

# add key bindings in .sublime-keymap file
# (none in this case: ys<arg>; y and s are standard Vim commands defined in Vintageous)

# actual command implementation
class _vi_plug_y_s(sublime_plugin.TextCommand):
    PAIRS = {
        '(': ('(', ')'),
        ')': ('( ', ' )'),
        '[': ('[', ']'),
        ']': ('[ ', ' ]'),
        '{': ('{', '}'),
        '}': ('{ ', ' }'),
    }
    def run(self, edit, mode=None, surround_with='"'):
        def f(view, s):
            if mode == _MODE_INTERNAL_NORMAL:
                self.surround(edit, s, surround_with)
                return s
            return s

        if surround_with:
            regions_transformer(self.view, f)

    def surround(self, edit, s, surround_with):
        open_, close_ = _vi_plug_y_s.PAIRS.get(surround_with, (surround_with, surround_with))

        if open_.startswith('<'):
            name = open_[1:].strip()[:-1]
            name = name.split(' ', 1)[0]
            self.view.insert(edit, s.b, "</{0}>".format(name))
            self.view.insert(edit, s.a, surround_with)
            return

        self.view.insert(edit, s.b, close_)
        self.view.insert(edit, s.a, open_)
