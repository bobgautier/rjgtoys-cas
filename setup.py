#!/usr/bin/python

# See: http://pythonhosted.org/an_example_pypi_project/setuptools.html

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# See: http://pytest.org/latest/goodpractises.html

from setuptools.command.test import test as TestCommand
import sys

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        import coverage
        import time
        import re
        
        package = 'cas'      # FIXME - get this from setup params
        
        cov_file = os.path.join(os.path.dirname(__file__),'.coverage')
        if os.path.exists(cov_file):
            os.unlink(cov_file)

        cov = coverage.coverage(include=['%s/*' % (package),'tests/unit/fixture*'])
        cov.start()
        errno = pytest.main(self.test_args)
        cov.stop()
        cov.save()
        cov_title = "Coverage report for %s created at %s" % (package,time.strftime("%Y-%m-%d %H:%M:%S"))
        
        cov_dir = os.path.join(os.path.dirname(__file__),'htmlcov')
        cov.html_report(directory=cov_dir)
            
        # Now fix up the report to have a nice title
        
        index_html = os.path.join(cov_dir,'index.html')
        
        report = open(index_html).read()
        report = re.sub('Coverage report',cov_title,report)
        
        with open(index_html,"w") as f:
            f.write(report)
        
        sys.exit(errno)


setup(
    name = "cas",
    version = "0.0.1",
    author = "Bob Gautier",
    author_email = "bob@rjg-resources.com",
    description = ("Content-addressable storage"),
    long_description = read('README'),
    license = "GPL",
    keywords = "cas",
    packages = ['cas'],
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)"
        ],
    tests_require=['pytest'],
    cmdclass = {'test':PyTest},

)
