
import sys
import urllib, urllib2

try:
    import simplejson as json
except ImportError:
    import json

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
NEWA_METADATA = CONFIG.networks.newa.metadata
WEB_SERVICE = CONFIG.web_services.newa

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NewaWebServicesClient(object):

    def __init__(self, base_url=WEB_SERVICE, debug=False):

        if base_url.endswith('/'):
            self.base_url = base_url
        else:
            self.base_url = base_url + '/'
        self.debug = debug

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def request(self, command, *args):
        ERRMSG = 'Error processing request : %s %s'

        if not command.endswith('/'): command += '/'

        url = self.base_url
        url += command + '/'.join(args)
        try:
            response = urllib2.urlopen(url)
        except Exception as e:
            setattr(e, 'details', ERRMSG % ('GET',url))
            raise e

        try:
            response_string = response.read()
        except Exception as e:
            setattr(e, 'details', ERRMSG % ('GET',url))
            raise e

        if response_string.startswith('Error processing request'):
            raise urllib2.HTTPError(response.geturl(), 404,
                                    ERRMSG % ('GET',url), None, None)

        try:
           result_dict = json.loads(response_string)
        except Exception as e:
            errmsg = 'unable to handle improperly formated JSON from server.\n'
            errmsg += response.geturl() + '\n'
            errmsg += '%s\nReturned JSON = %s' % (url,response_string)
            setattr(e, 'details', errmsg)
            raise e

        return result_dict['stations']
