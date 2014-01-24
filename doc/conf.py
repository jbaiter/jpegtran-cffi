# -*- coding: utf-8 -*-
import os, sys

sys.path.insert(0, '../')


class Mock(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

    @classmethod
    def __getattr__(cls, name):
        print "Getting mock: ", name
        if name in ('__file__', '__path__'):
            return '/dev/null'
        # Special case for CFFI
        elif name == 'FFI':
            return Mock()
        elif name[0] == name[0].upper():
            mockType = type(name, (), {})
            mockType.__module__ = __name__
            return mockType
        else:
            return Mock()

MOCK_MODULES = ['cffi']
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = u'jpegtran-cffi'
copyright = u'2014, Johannes Baiter'
version = '0.3'
release = '0.3.1'

exclude_patterns = ['_build']
pygments_style = 'sphinx'

html_static_path = ['_static']
htmlhelp_basename = 'jpegtran-cffidoc'

latex_elements = {
    'preamble': '',
}

latex_documents = [
    ('index', 'jpegtran-cffi.tex', u'jpegtran-cffi Documentation',
     u'Johannes Baiter', 'manual'),
]

man_pages = [
    ('index', 'jpegtran-cffi', u'jpegtran-cffi Documentation',
     [u'Johannes Baiter'], 1)
]

texinfo_documents = [
    ('index', 'jpegtran-cffi', u'jpegtran-cffi Documentation',
     u'Johannes Baiter', 'jpegtran-cffi', 'One line description of project.',
     'Miscellaneous'),
]
