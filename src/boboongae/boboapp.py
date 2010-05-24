from google.appengine.api import users
from google.appengine.ext import db

import bobo
import chameleon.zpt.loader
import os


template_path = os.path.join(os.path.dirname(__file__), 'templates')

template_loader = chameleon.zpt.loader.TemplateLoader(
    template_path,
    auto_reload=os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'))


class BoboData(db.Model):
    string = db.StringProperty()

    def json(self):
        return "{'string': %s}" % self.string


@bobo.query('/')
def index():
    BoboData(key_name="foobar", string="foobar").put()
    template = template_loader.load('index.html')
    user = users.get_current_user()
    return template(user=user)
