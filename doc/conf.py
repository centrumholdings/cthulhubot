# -*- coding: utf-8 -*-
import sys, os

extensions = ['sphinx.ext.autodoc']
templates_path = ['.templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'Django: massive buildbot'
copyright = u'2009, Centrum Holdings'

import djangomassivebuildbot as soft

version = ".".join(map(str, soft.__version__[:-1]))
release = soft.__versionstr__
