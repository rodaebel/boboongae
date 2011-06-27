=================================================
Using the Bobo Web Framework on Google App Engine
=================================================

Bobo is a light-weight framework for creating WSGI web applications. This demo
shows how to run it on Google App Engine.

See http://bobo.digicool.com/ for further information on bobo.


Running the application out of the box
--------------------------------------

Build and run the application::

  $ python bootstrap.py --distribute
  $ ./bin/buildout
  $ ./bin/dev_appserver parts/boboongae

Then access the application using a web browser with the following URL::

  http://localhost:8080/


Running tests
-------------

In order to run all functional tests enter the following command::

  $ bin/nosetests


Uploading and managing
----------------------

To upload application files, run::

  $ ./bin/appcfg update parts/boboongae

For a more detailed documentation follow this url::

  http://code.google.com/appengine/docs/python/tools/uploadinganapp.html
