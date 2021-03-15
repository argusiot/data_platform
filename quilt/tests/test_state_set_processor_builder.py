'''
    test_set_processor_builder.py

    Test cases for SetProcessorBuilder class
'''
import sys
import os

# FIXME: We're cheating a little here until we've sorted out how to 
# package applique_infra (i.e. inside argus_tal or separately outside).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../applique_infra')))
from state_set_processor_builder import StateSetProcessorBuilder

import unittest
from unittest import mock

class SetProcessorBuilder_Tests(unittest.TestCase):
  '''Unit tests for SetProcessorBuilder.'''

