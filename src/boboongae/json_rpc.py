# -*- coding: utf-8 -*-
#
# Copyright 2010 Florian Glanzner (fgl)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
JSONRPCHandler.
A webapp.RequestHandler for TyphoonAE and Google App Engine
See specs:
http://groups.google.com/group/json-rpc/web/json-rpc-2-0
http://groups.google.com/group/json-rpc/web/json-rpc-over-http

This version does not support:
  - *args, **kwargs and default-values are not supported for Service Methods
  - Handle only HTTP POST
  - json-rpc Version < 2.0 (same as 1.2) not handled

TODO:
 - more Comments
 - Examples (doctest?)
 - ...
"""
import cgi
import logging
import sys
import traceback
from django.utils.simplejson import dumps, loads
from google.appengine.ext import webapp
from inspect import getargspec

def ServiceMethod(fn):
    """
    Decorator to mark a method of a JSONRPCHAndler as ServiceMethod.
    This exposes methods to the rpc interface.
    TODO:
        - Warn when applied to underscore methods
    """
    fn.IsServiceMethod = True
    return fn

class JsonRpcError(Exception):
    """
    Baseclass for all JSON-RPC Errors.
    Errors are described in the JSON-RPC 2.0 specs, related HTTP Status
    Codes are described in the json-rpc-over-http proposal.
    """
    code = 0
    message = None
    data = None
    status = 500

    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def __str__(self):
        return(self.message)

    def __repr__(self):
        return '%s("%s")' % (str(self.__class__.__name__), self.message)

    def getJsonData(self):
        error = {
            'code' : self.code ,
            'message' : '%s: %s' %
                (str(self.__class__.__name__),
                str(self.message))}
        if self.data is not None:
            error['data'] = self.data
        # TODO More / less info depending on DEBUG mode
        return error
        
class ParseError(JsonRpcError):
    """
    Invalid JSON was received by the server.
    An error occurred on the server while parsing the JSON text.
    """
    code = -32700
    message = 'Parse error.'

class InvalidRequestError(JsonRpcError):
    """
    The JSON sent is not a valid Request object.
    """
    code = -32600
    message = 'Invalid Request.'
    status = 400

class MethodNotFoundError(JsonRpcError):
    """
    The method does not exist / is not available.
    """
    code = -32601
    message = 'Method not found.'
    status = 404

class InvalidParamsError(JsonRpcError):
    """
    Invalid method parameter(s).
    """
    code = -32602
    message = 'Invalid params'

class InternalError(JsonRpcError):
    """
    Internal JSON-RPC error.
    """
    code = -32603
    message = 'Internal error.'

class ServerError(JsonRpcError):
    """
    Base Class for implementation-defined Server Errors.
    The Error Code must be between -32099..-32000
    """
    code = -32000
    message = 'Server Error'

class JsonRpcMessage(object):
    """A single json-rpc message"""
    def __init__(self, json=None):
        super(JsonRpcMessage, self).__init__()
        self.message_id = None
        self.notification = False
        self.error = None
        self.result = None
        if json is not None:
            self.from_json(json)

    def from_json(self, json):
        """Parses a single json-rpc message"""
        try:
            if not isinstance(json, dict):
                raise InvalidRequestError(
                        'No valid JSON-RPC Message. Must be an object.')

            if not set(json.keys()) <= frozenset(
                    ['method','jsonrpc','params','id']):
                raise InvalidRequestError('Invalid members in request object')

            if not ('jsonrpc' in json and json['jsonrpc'] == '2.0'):
                raise InvalidRequestError(
                        'Server support JSON-RPC Ver. 2.0 only')

            if 'method' not in json:
                raise InvalidRequestError('No method specified')
            if not isinstance(json['method'], basestring):
                raise InvalidRequestError('method must be a string')
            self.method_name = json['method']

            if 'params' in json:
                params = json['params']
                if not isinstance(params, (dict, list, tuple)):
                    raise InvalidRequestError(
                            '"params" must be an array or object.')
                self.params = params

            if 'id' not in json:
                self.notification = True
            else:
                self.message_id = json['id']
        except InvalidRequestError, ex:
            self.error = ex
            logging.info('Encountered invalid json message: ')

class JsonRpcHandler(webapp.RequestHandler):
    """
    Subclass this handler to implement a json-rpc handler.
    Annotate methods with @ServiceMethod to expose them and make them callable
    via json-rpc. Currently methods with *args or **kwargs are not supported
    as service-methods. All parameters have to be named explicitly.
    """
    
    def __init__(self):
        webapp.RequestHandler.__init__(self)

    def post(self):
        self.handle_request()

    def handle_request(self):
        """
        handles post request
        """
        self.response.headers['Content-Type'] = 'application/json-rpc'
        try:
            messages, batch_request = self.parse_body(self.request.body)
        except (InvalidRequestError, ParseError), ex:
            logging.info(ex)
            self.error(ex.status)
            body = self._build_error(ex)
            self.response.out.write(dumps(body))
        else:
            for msg in messages:
                self.handle_message(msg)

            responses = self.get_responses(messages)
            if len(responses) == 0:
                # Only notifications were sent
                self.error(204)
                return

            if batch_request:
                #TODO Which http_status to set for batches?
                self.error(200)
                body =  [r[1] for r in responses]
                self.response.out.write(dumps(body))
            else:
                if len(responses) != 1:
                    raise  InternalError() #this cannot happen
                status, body = responses[0]
                self.error(status)
                self.response.out.write(dumps(body))

    def get_responses(self, messages):
        """Gets a list of responses from all 'messages'.
        Responses are a tuple of http-status and body.
        A Response may be None if the message was a notification.
        None Responses are excluded from the returned list.
        """
        #return
        #[x for x in [m.getResponse() for m in messages] if x is not None]
        responses = []
        for msg in messages:
            resp = self.get_response(msg)
            if resp is not None:
                responses.append(resp)
        return responses

    def handle_message(self, msg):
        """Executes a message.
        The method of the message is executed.
        Errors and/or result are written back to the message.
        """
        if msg.error != None:
            return
        else:
            try:
                method = self.get_service_method(msg.method_name)
                params = getattr(msg, 'params', None)
                msg.result = self.execute_method(method, params)
            except (MethodNotFoundError, 
                    InvalidParamsError,
                    ServerError ), ex:
                logging.info(ex)
                msg.error = ex
            except Exception, exc:
                logging.error(exc)
                ex = InternalError("Error executing Service Method")
                ex.data = ''.join(traceback.format_exception(*sys.exc_info()))
                msg.error = ex

    def parse_body(self, body):
        """Parses the body of post-request.
         Validates for correct json. 
         Returns a tuple with a list of json-rpc messages and wether the 
         request was a batch-request.
         Raises ParseError and InvalidRequestError.
        """
        try:
            json = loads(body)
        except ValueError:
            raise ParseError()

        messages = []
        if isinstance(json, (list, tuple)):
            if len(json) == 0:
                raise InvalidRequestError('Recieved an empty batch message.')
            batch_request = True
            for obj in json:
                msg = JsonRpcMessage(obj)
                messages.append(msg)

        if isinstance(json, (dict)):
            batch_request = False
            msg = JsonRpcMessage(json)
            messages.append(msg)
        return messages, batch_request

    def get_response(self, msg):
        """Gets the response object for a message.
        Returns a tuple of a http-status and a json object or None.
        The json object maybe a json-rpc error object a result object
        None is returned if the message was a notification.
        """
        if msg.notification:
            return None
        elif msg.error:
            return (msg.error.status, 
                    self._build_error(msg.error, msg.message_id))
        elif msg.result:
            return (200, self._build_result(msg))
        else:
            # should never be reached
            logging.warn('Message neither contains an error nor a result')

    def _build_error(self, err, message_id=None):
        return {'jsonrpc':'2.0',
                'error':err.getJsonData(),
                'id':message_id}
    def _build_result(self, msg):
        return {'jsonrpc':'2.0',
                'result':msg.result,
                'id':msg.message_id}

    def execute_method(self, method, params):
            args = set(getargspec(method)[0][1:])
            # import pdb; pdb.set_trace()
            if params is None:
                if not len(args) == 0:
                    raise InvalidParamsError("Wrong number of parameters. "+
                        "Expected %i but 'params' was omitted "%(len(args))+
                        "from json-rpc message.")
                return method()
            if isinstance(params, (list, tuple)):
                if not len(args) == len(params):
                    raise InvalidParamsError("Wrong number of parameters. "+
                        "Expected %i got %i."%(len(args),len(params)))
                return method(*params)
            if isinstance(params, dict):
                paramset = set(params)
                if not args == paramset:
                    raise InvalidParamsError("Named parameters do not "+
                        "match method. Expected %s."%(str(args)))
                params = self.decode_dict_keys(params)
                return method(**params)

    def get_service_method(self, meth_name):
        # TODO use inspect.getmembers()?
        f = getattr(self, meth_name, None)
        if f == None or \
                not hasattr(f, 'IsServiceMethod') or \
                not getattr(f, 'IsServiceMethod') == True:
            raise MethodNotFoundError('Method %s not found'%meth_name)
        return f

    def decode_dict_keys(self, d):
        """
        Convert all keys i dict d to str.
        Maybe Unicode in JSON but no Unicode as keys in python allowed
        """
        try:
            r = {}
            for (k, v) in d.iteritems():
                r[str(k)] = v
            return r
        except UnicodeEncodeError:
            # Unsure which error is the correct to raise here.
            # Actually this code will probably never be reached
            # because "wrong" parameters will be filtered out
            # and returned as InvalidParamsError() and methods cant
            # have non-ascii parameter names.
            raise InvalidRequestError("Parameter-names must be ASCII")
