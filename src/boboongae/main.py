"""Sample application for running the bobo web framework on GAE."""

import sys
sys.path.insert(0, 'packages.zip')

from bobo import Application
from google.appengine.ext.webapp import util


def main():
    util.run_wsgi_app(Application(bobo_resources='boboapp'))


if __name__ == '__main__':
    main()
