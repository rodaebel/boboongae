"""Testing boboongae."""

from google.appengine.ext import testbed

import bobo
import nose.tools
import os
import webtest


app = webtest.TestApp(bobo.Application(bobo_resources='boboapp'))


def setup_func():
    """Set up test fixtures."""

    # Create an instance of the Testbed class
    tb = testbed.Testbed()

    # Activate the testbed
    tb.activate()

    # We need an authenticated admin user
    tb.init_user_stub()


@nose.tools.with_setup(setup_func)
def test_index():
    """Testing whether our application responds"""

    response = app.get('/')
    nose.tools.assert_equal(response.status, '200 OK')
