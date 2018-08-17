from copy import copy

from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

NEWA_SIGNATURE = "NEWANEWANEWANEWANEWA\nDan Olmstead, Leader\nNetwork for Environment & Weather App's\nNYS IPM Program, Cornell University\ndlo6@cornell.edu\nhttp://newa.cornell.edu"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# sensors configuration hierarchy
#
#    sensors.email
#    sensors.email.constraints
#    sensors.email.search_criteria
#
#    sensors.email.content
#    sensors.email.content.error
#    sensors.email.content.error.html
#    sensors.email.content.error.html.pcpn
#    sensors.email.content.error.text
#    sensors.email.content.error.text.pcpn
#
#    sensors.email.content.summary
#    sensors.email.content.summary.details
#    sensors.email.content.summary.details.pcpn
#    sensors.email.content.summary.text
#
#    sensors.email.header
#    sensors.email.header.debug 
#    sensors.email.header.debug[bcc, cc, mail_to, sender, signature, subject]
#    sensors.email.header.error
#    sensors.email.header.error[bcc, cc, mail_to, sender, signature, subject]
#    sensors.email.header.summary
#    sensors.email.header.summary[bcc, cc, mail_to, sender, signature, subject]
#    sensors.email.header.test
#    sensors.email.header.test[bcc, cc, mail_to, sender, signature, subject]
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize sensor error detection configuration
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sensors = ConfigObject('sensors', None, 'email.header', 'email.content',
                       'email.content.error.html', 'email.content.error.text',
                       'email.content.summary.detail', 'pcpn')

# some attributes coomon to all sensors
sensors.constraints = (('network','!=','icao'),('active','=','Y'))
sensors.end_hour = 7
sensors.grid_offset = 0.0625 # 5 x 5 grid, 20 km**2
sensors.search_criteria = (('network','!=','icao'),)
sensors.start_hour = 8
sensors.station_metadata =\
        'sid,name,ucanid,active,network,lat,lon,first_hour,last_report'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# precip specific attributes
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sensors.pcpn.grid_threshold = 0.1 # 0.05
sensors.pcpn.missing_threshold = 1
sensors.pcpn.resample_padding = 6
sensors.pcpn.station_threshold = 0.1 # 0.05 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize sensors email headers and content
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sensors.email.header.debug = {
           'sender'  : 'Northeast Regional Climate Center Test Server <nrcc@cornell.edu>',
           'mail_to' : 'Rick Moore <rem63@cornell.edu>',
           'cc'      : None,
           'bcc'     : None,
           }

sensors.email.header.test = {
           'sender'  : 'Northeast Regional Climate Center Test Server <nrcc@cornell.edu>',
           'mail_to' : 'Art DeGaetano <atd2@cornell.edu>',
           'cc'      : 'Rick Moore <rem63@cornell.edu>',
           'bcc'     : None,
           }

sensors.email.header.error = {
           'subject' : 'NEWA Station %(name)s Rain Gauge Error',
           'sender'  : 'Dan Olmstead <dlo6@cornell.edu>',
           'mail_to' : '%(contact)s <%(email)s>',
           'cc'      : '%(bcontact)s <%(bemail)s',
           'bcc'     : None,
           'signature' : NEWA_SIGNATURE,
           }

sensors.email.header.summary = {
           'subject' : 'Summary Report',
           'sender'  : 'Northeast Regional Climate Center <nrcc@cornell.edu>',
           'mail_to' : 'Keith Eggleston <keith.eggleston@cornell.edu>, Dan Olmstead <dlo6@cornell.edu>',
           'cc'      : 'Art DeGaetano <atd2@cornell.edu>',
           'bcc'     : 'Rick Moore <rem63@cornell.edu>',
           'signature' : 'NRCC - Northeast Regional Climate Center',
           'title'   : '\nWeather stations that did not report :',
           }


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for precip sensor errors
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sensors.email.content.error.html.pcpn = """
<html xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>Precipitation data received by NEWA from your weather station at %(name)s shows likely errors for the 24 hour period ending %(period_end)s.</h3>
<p>The tipping bucket rain gauge on your weather station is reporting data that is either out-of-range, missing or in error. Please check your weather instrument to troubleshoot the problem. </p>
<p>Specific maintenance information for rain gauges is available on the <a href="http://newa.cornell.edu/index.php?page=maintenance-guidelines">"Maintenance Guidelines" web page</a> at the NEWA website.</p>
<p>To prevent abnormal data being sent to NEWA during maintenance procedures, turn off the weather station before cleaning or repairing the rain gauge and turn it back on when maintenance is complete.</p>
<p>If the system has been checked and appears to be working, but accurate data is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>, please contact the weather station manufacturer.</p>
<p><b>If you feel that you received this email in error, please contact <a href="mailto:dlo6@cornell.edu?Subject=Precipitation%%20Data%%20Error%%20Notification%%20recieved%%20for%%20%(sid)s:%(name)s">Dan Olmstead</a>, New York State IPM Program.</b></p>
%(signature)s
</div> </body> </html>
"""

sensors.email.content.error.text.pcpn = """
Precipitation data received by NEWA from your weather station at %(name)s shows likely errors for the 24 hour period ending %(period_end)s.

The tipping bucket rain gauge on your weather station is reporting data that is either out-of-range, missing or in error. Please check your weather instrument to troubleshoot the problem.

Specific maintenance information for rain gauges is available on the "Maintenance Guidelines" web page on the NEWA website at http://newa.cornell.edu/index.php?page=maintenance-guidelines

To prevent abnormal data being sent to NEWA during maintenance procedures, turn off the weather station before cleaning or repairing the rain gauge and turn it back on when maintenance is complete.

If the system has been checked and appears to be working, but accurate data is still not being displayed on the NEWA website (http://newa.cornell.edu/"), please contact the weather station manufacturer.

If you feel that you received this email in error, please send an email to Dan Olmstead <dlo6@cornell.edu> with the subject : "Precipitation Data Error Notification recieved for %(sid)s:%(name)s", New York State IPM Program.</b></p>

%(signature)s
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for sensor error summary
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sensors.email.content.summary.contact = """       Email sent to %(contact)s @ %(email)s"""
sensors.email.content.summary.station = """    %(network)s station : %(sid)s : %(name)s"""
sensors.email.content.summary.text = """
%(summary)s
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of summary content for each sensor
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sensors.email.content.summary.detail.pcpn = """     Rain gauge error for 24 hrs ending %(last_time)s"""

