"""Sample application for running the bobo web framework on GAE."""

from bobo import Application
from google.appengine.ext.webapp import util


def main():
    util.run_wsgi_app(Application(bobo_resources='boboapp'))


if __name__ == '__main__':
    main()
