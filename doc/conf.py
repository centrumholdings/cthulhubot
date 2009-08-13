# -*- coding: utf-8 -*-
import sys, os

extensions = ['sphinx.ext.autodoc']
templates_path = ['.templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'CthulhuBot'
copyright = u'2009, Centrum Holdings'

import cthulhubot as project

version = ".".join(map(str, project.__version__[:-1]))
release = project.__versionstr__
