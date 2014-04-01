
import sublime
import sublime_plugin

from itertools import chain
import os
import unittest

from Vintageous.test_runner import OutputPanel


TEST_ACTIONS = 'Vintageous_Plugin_Surround.tests.test_action_cmds'


test_suites = {
        'actions': ['_pt_run_vintageous_surround_tests', [
                                        TEST_ACTIONS,
                                        ]],
}


# Combine all tests under one key for convenience. Ignore keys starting with
# an underscore. Use these for subsets of all the remaining tests that you
# don't want repeated under '_all_'. Convert to list so the 'chain' doesn't
# get exhausted after the first use.
all_tests = list(chain(*[data[1] for (key, data) in test_suites.items() if not key.startswith('_')]))
test_suites['_all_'] = ['_pt_run_vintageous_surround_tests', all_tests]


class ShowVintageousPluginSurroundTestSuites(sublime_plugin.WindowCommand):
    """Displays a quick panel listing all available test stuites.
    """
    def run(self):
        self.window.show_quick_panel(sorted(test_suites.keys()), self.run_suite)

    def run_suite(self, idx):
      if idx == -1:
        return

      suite_name = sorted(test_suites.keys())[idx]
      command_to_run, names = test_suites[suite_name]

      self.window.run_command('_pt_run_vintageous_surround_tests', {'suite_names': names})


class _ptRunVintageousSurroundTests(sublime_plugin.WindowCommand):
    def run(self, suite_names):
        # _, suite_names = test_suites[TestsState.suite]
        suite = unittest.TestLoader().loadTestsFromNames(suite_names)

        bucket = OutputPanel('vintageous.tests')
        bucket.show()
        runner = unittest.TextTestRunner(stream=bucket, verbosity=1)
        sublime.set_timeout_async(lambda: runner.run(suite), 0)
