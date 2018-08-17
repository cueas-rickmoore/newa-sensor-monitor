
import sys
import itertools
import urllib, urllib2
from datetime import datetime
from datetime import date as datetime_date

try:
    import simplejson as json
except ImportError:
    import json

import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from rccpy.acis.config import CONFIG
SERVER_URL = CONFIG.default_server_url

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BaseAcisClient:

    def __init__(self, server_url=SERVER_URL, **kwargs):

        if server_url.endswith('/'): self.server_url = server_url[:-1]
        else: self.server_url = server_url
        self.debug = kwargs.get('debug',False)
        self.keyword_args = kwargs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def request(self, request_type, request_params):

        url = '%s/%s' % (self.server_url, request_type)
        post_params = urllib.urlencode({'params':request_params})

        if self.debug:
            print 'POST', url
            print 'params =', request_params
        req = urllib2.Request(url, post_params, {'Accept':'application/json'})

        url += ' json=' + request_params
        try:
            response = urllib2.urlopen(req)
        except:
            print 'Error processing request : %s' %  url
            raise

        return response

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, request_type, request_params):
        response = self.request(request_type, request_params)
        data, errors = self._serialize(response)
        if errors:
            data['request url'] = reposnse.getUrl()
            data['server errors'] = errors
        return data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _serialize(self, response):
        try:
            response_data = response.read()
        except:
            errmsg = 'Error was encountered while reading response to : %s'
            print errmsg % response.response.geturl() 

        json_str, errors = self._validateResponseData(response_data, response)
        try:
           data = json.loads(json_str)
        except:
            errmsg += 'Unable to parse improperly formated JSON from server.\n'
            errmsg += response.geturl() + '\n' + json_str
            raise ValueError, errmsg

        return data, errors

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validateResponseData(self, response_data, response):
        if 'DOCTYPE HTML PUBLIC' in response_data:
            errmsg = 'SERVER ERROR : '
            if 'server encountered an internal error' in response_data:
                errmsg = 'Server encountered an unspecified internal error.'
                ecode = 503
            else:
                ecode = 500
                errmsg += 'Server returned HTML, not valid JSON.\n'
                errmsg += '\n%s' % response_data
            raise urllib2.HTTPError(response.geturl(),ecode,errmsg,None,None)

        server_error = 'SERVER ERROR : '
        errors = [ ]
        if '[Failure instance:' in response_data:
            found_start = response_data.find('[Failure instance:')
            while found_start > 0:
                found_end = response_data.find('\n],',found_start)
                error = response_data[found_start:found_end+3]
                errors.append(''.join(error.splitlines()))
                before = response_data[:found_start]
                after = response_data[found_end+3:]
                response_data = before + after
                found_start = response_data.find('[Failure instance:')

        if errors:
            errmsg = 'The following errors found in the JSON string returned'
            errmsg += ' for request : %s' response.getUrl()
            print server_error, errmsg
            for error in errors:
                print error
            errmsg = 'The resulting station data block may be incomplete.'
            sys.stdout.flush()

       return response_data, errors

