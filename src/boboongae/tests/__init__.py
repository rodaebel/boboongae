"""Testing boboongae."""

import bobo
import nose.tools
import os
import webtest


app = webtest.TestApp(bobo.Application(bobo_resources='boboapp'))


def setup_func():
    """Set up test fixtures."""

    os.environ['USER_EMAIL'] = 'bobo@bobo.net'


@nose.tools.with_setup(setup_func)
def test_index():
    """Testing whether our application responds"""

    response = app.get('/')
    nose.tools.assert_equal(response.status, '200 OK')
