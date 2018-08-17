
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from httplib import HTTP 
from urlparse import urlparse 

def urlExists(url): 
     parsed_url = urlparse(url)
     http = HTTP(parsed_url[1]) 
     http.putrequest('HEAD', parsed_url[2]) 
     http.endheaders() 
     reply = http.getreply()
     if reply[0] == 200:
         return True
     return False

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

