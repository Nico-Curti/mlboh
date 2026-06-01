#!/usr/bin/python
# -*- coding: utf-8 -*-

from .__version__ import __version__
from .mlboh import manual_parallel_cv_threads
from .mlboh import manual_parallel_cv_processes

__author__ = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

__all__ = [
  '__version__',
  'manual_parallel_cv_threads',    
  'manual_parallel_cv_processes',
]
