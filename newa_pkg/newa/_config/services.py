
from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize configuration of services
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

services = ConfigObject('services',None,'web','email')

services.web.acis = 'http://data.rcc-acis.org/'
services.web.newa = 'http://newa.nrcc.cornell.edu/newaUtil/'
#services.email.smtp_host = 'virga.nrcc.cornell.edu'
services.email.smtp_host = 'appsmtp.mail.cornell.edu'

