import sys
sys.path.insert(0, 'packages.zip')

from boboapp import BoboData
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from json_rpc import JsonRpcHandler, ServiceMethod


class RPCHandler(JsonRpcHandler):
    """Handles Remote Procedure Calls.

    No need to define post().
    """

    @ServiceMethod
    def data(self, key_name):
        entity = BoboData.get_by_key_name(key_name)
        if entity:
            return entity.json()


app = webapp.WSGIApplication([
    ('/rpc', RPCHandler),
], debug=True)


def main():
    """The main function."""

    webapp.util.run_wsgi_app(app)


if __name__ == '__main__':
    main()
