from copy import copy

from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# rem63 20180608 - per Dan olmstedt - new, simpler signature
NEWA_SIGNATURE = {
    'html':'All the best.<br/>Dan Olmstead<br/>NEWA Coordinator<br/><a href="mailto:support@newa.zendesk.com?Subject=Weather%%20station%%20at%%20%(name)s,%(state)s%%20(%(sid)s)">support@newa.zendesk.com</a>',
    'text':'All the best.\nDan Olmstead\nNEWA Coordinator\nsupport@newa.zendesk.com',
}
# rem63 20180608 - per Dan olmstedt - new support email address
NEWA_SUPPORT = 'support@newa.zendesk.com <support@newa.zendesk.com>'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# validation configuration hierarchy
#
#    validation.email
#    validation.email.constraints
#    validation.email.search_criteria
#
#    validation.email.content
#    validation.email.content.station
#    validation.email.content.station.activate
#    validation.email.content.station.activate.html[cellular, default, ip-100, ftp, modem]
#    validation.email.content.station.activate.text[cellular, default, ip-100, ftp, modem]
#    validation.email.content.station.deactivate
#    validation.email.content.station.deactivate.html[cellular, default, ip-100, ftp, modem]
#    validation.email.content.station.deactivate.text[cellular, default, ip-100, ftp, modem]
#    validation.email.content.station.missing
#    validation.email.content.station.missing.html[cellular, default, ip-100, ftp, modem]
#    validation.email.content.station.missing.text[cellular, default, ip-100, ftp, modem]
#
#    validation.email.content.summary
#    validation.email.content.summary.contact
#    validation.email.content.summary.station
#    validation.email.content.summary.activate
#    validation.email.content.summary.activate.detail
#    validation.email.content.summary.activate.text
#    validation.email.content.summary.deactivate
#    validation.email.content.summary.deactivate.detail
#    validation.email.content.summary.deactivate.text
#    validation.email.content.summary.missing
#    validation.email.content.summary.missing.detail[Y, O]
#    validation.email.content.summary.missing.text
#
#    validation.email.header
#    validation.email.header.activate
#    validation.email.header.activate[bcc, cc, mail_to, sender, signature, subject]
#    validation.email.header.deactivate
#    validation.email.header.deactivate[bcc, cc, mail_to, sender, signature, subject]
#    validation.email.header.debug 
#    validation.email.header.debug[bcc, cc, mail_to, sender, signature, subject]
#    validation.email.header.missing
#    validation.email.header.missing[bcc, cc, mail_to, sender, signature, subject]
#    validation.email.header.summary
#    validation.email.header.summary[bcc, cc, mail_to, sender, signature, subject]
#    validation.email.header.test
#    validation.email.header.test[bcc, cc, mail_to, sender, signature, subject]
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize validation configuration
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation = ConfigObject('validation', None)
validation.constraints = (('network','!=','icao'),('active','=','Y'))
validation.search_criteria = (('network','!=','icao'),)

# station.(activate or deactivate or missing).(html or text)
activate = ConfigObject('activate', None, 'html', 'text')
deactivate = ConfigObject('deactivate', None, 'html', 'text')
missing = ConfigObject('missing', None, 'html', 'text')
station = ConfigObject('station', None, activate, deactivate, missing)
del activate, deactivate, missing

# summary.(activate or deactivate or missing)
summary = ConfigObject('summary', None, 'activate', 'deactivate', 'missing')

# content.(station or summary)
content = ConfigObject('content', None, station, summary)
# validaton.email.(header or content)
validation.addChild(ConfigObject('email', None, 'header', content))
del content

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize validation.email.header
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation.email.header.debug = {
           'sender'  : 'Northeast Regional Climate Center Test Server <nrcc@cornell.edu>',
           'mail_to' : 'Rick Moore <rem63@cornell.edu>',
           'cc'      : None,
           'bcc'     : None,
           }

# rem63 - per Dan Olmstedt - add station id (sid) to subject line
validation.email.header.error = {
           'subject' : 'ERROR : NEWA Station %(name)s, %(state)s (%(sid)s)',
           'sender'  : 'NRCC Newa Validation Server <nrcc@cornell.edu>',
           'mail_to' : 'Keith Eggleston <keith.eggleston@cornell.edu>',
           'cc'      : 'Rick Moore <rem63@cornell.edu>, Art DeGaetano <atd2@cornell.edu>',
           'bcc'     : None,
           'signature' : 'NRCC Newa Validation Server',
           }

validation.email.header.test = {
           'sender'  : 'Northeast Regional Climate Center Test Server <nrcc@cornell.edu>',
           'mail_to' : 'Rick Moore <rem63@cornell.edu>',
           'cc'      : None,
           'bcc'     : None,
           }

# rem63 - per Dan Olmstedt - add station id (sid) to subject line
validation.email.header.missing = {
           'subject' : 'NEWA Station %(name)s, %(state)s (%(sid)s) : Outage Report for %(report_date)s',
           'sender'  : NEWA_SUPPORT,
           'mail_to' : '%(contact)s <%(email)s>',
           'cc'      : '%(bcontact)s <%(bemail)s>',
           'bcc'     : None,
           'signature' : '%(signature)s',
           'title'   : '\nWeather stations that did not report :',
           }
validation.email.header.out_24_hours = validation.email.header.missing
validation.email.header.out_7_days = validation.email.header.missing

validation.email.header.action_required = {
           'subject' : 'NEWA Station(s) Require Adminstrative Action',
           'sender'  : 'Northeast Regional Climate Center <nrcc@cornell.edu>',
           'mail_to' : 'Jessica Spacio <jlr98@cornell.edu>, Samantha Borisoff <sgh58@cornell.edu>',
           'cc'      : 'Keith Eggleston <keith.eggleston@cornell.edu>',
           'bcc'     : 'Rick Moore <rem63@cornell.edu>',
           'signature' : 'NRCC - Northeast Regional Climate Center'
           }

# rem63 - per Dan Olmstedt - add station id (sid) to subject line
validation.email.header.activate = {
        'subject' : 'NEWA Station %(name)s, %(state)s (%(sid)s) : Activation Report for %(report_date)s',
           'sender'  : NEWA_SUPPORT,
           'mail_to' : '%(contact)s <%(email)s>',
           'cc'      : '%(bcontact)s <%(bemail)s>',
           'bcc'     : None,
           'signature' : '%(signature)s',
           'title'   : '\nStations that should have active status changed to "Yes" :',
           }

# rem63 - per Dan Olmstedt - add station id (sid) to subject line
validation.email.header.deactivate = {
           'subject' : 'NEWA Station %(name)s, %(state)s (%(sid)s) : Outage Report for %(report_date)s',
           'sender'  : NEWA_SUPPORT,
           'mail_to' : '%(contact)s <%(email)s>',
           'cc'      : '%(bcontact)s <%(bemail)s>',
           'bcc'     : None,
           'signature' : '%(signature)s',
           'title'   : '\nStations that should have active status changed to "Out" :',
           }

validation.email.header.summary = {
           'subject' : 'Summary of weather stations with reporting issues on %(report_date)s',
           'sender'  : 'Northeast Regional Climate Center <nrcc@cornell.edu>',
           'mail_to' : 'Keith Eggleston <keith.eggleston@cornell.edu>, Dan Olmstead <dlo6@cornell.edu>',
           'cc'      : 'Art DeGaetano <atd2@cornell.edu>, Nicole Mattoon <nem42@cornell.edu>',
           'bcc'     : 'Rick Moore <rem63@cornell.edu>',
           'signature' : 'NRCC - Northeast Regional Climate Center'
           }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for contet.station.activate
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation.email.content.station.activate.html['ip-100'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>

<p><b>If you feel that you received this email in error, please contact <a href="dlo6@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s:%(state)s">Dan Olmstead</a>, New York State IPM Program.</b></p>
%(signature)s
"""

validation.email.content.station.activate.text['ip-100'] = """
%(tag_line)s

%(signature)s
"""

validation.email.content.station.activate.html.ftp = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>

<p><b>If you feel that you received this email in error, please contact <a href="dlo6@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s:%(state)s">Dan Olmstead</a>, New York State IPM Program.</b></p>
%(signature)s
"""

validation.email.content.station.activate.text.ftp = """
%(tag_line)s

%(signature)s
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for contet.station.deactivate
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# rem63 20180608 - per Dan Olmstedt - replace content of deactivate (21 day) message
validation.email.content.station.deactivate.html.default = """
<html xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<p>Your %(name)s, %(state)s (%(sid)s) weather station has been out of communication for 21 days and a work ticket has been created by the NEWA help desk. We are temporarily disabling your weather station to prevent inaccurate NEWA model results.</p>
<p>Please reply to this message for assistance or to report the issue as solved. We are happy to troubleshoot the problem or refer the incident directly to your weather station vendor for quick resolution.</p>
%(signature)s
</div> </body> </html>
"""
# rem63 20180608 - per Dan Olmstedt - messages are no longer specific to a particular sensor
validation.email.content.station.deactivate.html['ip-100'] = validation.email.content.station.deactivate.html.default
validation.email.content.station.deactivate.html.cellular = validation.email.content.station.deactivate.html.default
validation.email.content.station.deactivate.html.ftp = validation.email.content.station.deactivate.html.default
validation.email.content.station.deactivate.html.modem = validation.email.content.station.deactivate.html.default


# rem63 20180608 - per Dan Olmstedt - replace deactivate (21 day message)
validation.email.content.station.deactivate.text.default = """
Your %(name)s, %(state)s (%(sid)s) weather station has been out of communication for 21 days and a work ticket has been created by the NEWA help desk. We are temporarily disabling your weather station to prevent inaccurate NEWA model results.

Please reply to this message for assistance or to report the issue as solved. We are happy to troubleshoot the problem or refer the incident directly to your weather station vendor for quick resolution.

%(signature)s
"""
# rem63 20180608 - per Dan Olmstedt - messages are no longer specific to a particular sensor
validation.email.content.station.deactivate.text['ip-100'] = validation.email.content.station.deactivate.text.default
validation.email.content.station.deactivate.text.cellular = validation.email.content.station.deactivate.text.default
validation.email.content.station.deactivate.text.ftp = validation.email.content.station.deactivate.text.default
validation.email.content.station.deactivate.text.modem = validation.email.content.station.deactivate.text.default


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for instances of station missing
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# rem63 20180608 - per Dan Olmstedt - replace single "missing" message with
#                  separate messages for out_24_hours and out_7_days notices.
# HTML version of 24 hour message
validation.email.content.station['out_24_hours.html.default'] = """
<html xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<p>Your %(name)s, %(state)s (%(sid)s) weather station has been out of communication for 24 hours and a work ticket has been created by the NEWA help desk. We are happy to troubleshoot the problem or refer the incident directly to your weather station vendor for quick resolution.</p>
<p>Please reply to this message for assistance or to report the issue as solved.</p>
<p>A second message will be sent at 7 days if we are unable to reach you. A third and final notification will be sent at 21 days. Your weather station will be temporarily disabled at that time to prevent inaccurate NEWA model results.<\p>
%(signature)s
</div> </body> </html>
"""
# rem63 20180608 - per Dan Olmstedt - messages are no longer specific to a particular sensor
validation.email.content.station.out_24_hours.html['ip-100'] = validation.email.content.station.out_24_hours.html.default
validation.email.content.station.out_24_hours.html.cellular = validation.email.content.station.out_24_hours.html.default
validation.email.content.station.out_24_hours.html.ftp = validation.email.content.station.out_24_hours.html.default
validation.email.content.station.out_24_hours.html.modem = validation.email.content.station.out_24_hours.html.default


# rem63 20180608 - per Dan Olmstedt - replace single "missing" message with
#                  separate messages for out_24_hours and day_7 notices.
# TEXT version of 24 hour message
validation.email.content.station['out_24_hours.text.default'] = """
Your %(name)s, %(state)s (%(sid)s) weather station has been out of communication for 24 hours and a work ticket has been created by the NEWA help desk. We are happy to troubleshoot the problem or refer the incident directly to your weather station vendor for quick resolution.

Please reply to this message for assistance or to report the issue as solved. 

A second message will be sent at 7 days if we are unable to reach you. A third and final notification will be sent at 21 days. Your weather station will be temporarily disabled at that time to prevent inaccurate NEWA model results.

%(signature)s
"""
# rem63 20180608 - per Dan Olmstedt - messages are no longer specific to a particular sensor
validation.email.content.station.out_24_hours.text['ip-100'] = validation.email.content.station.out_24_hours.text.default
validation.email.content.station.out_24_hours.text.cellular = validation.email.content.station.out_24_hours.text.default
validation.email.content.station.out_24_hours.text.ftp = validation.email.content.station.out_24_hours.text.default
validation.email.content.station.out_24_hours.text.modem = validation.email.content.station.out_24_hours.text.default


# rem63 20180608 - per Dan Olmstedt - replace single "missing" message with
#                  separate messages for out_24_hours and day_7 notices.
# HTML version of 7 day message
validation.email.content.station['out_7_days.html.default'] = """
<html xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<p>Your  %(name)s, %(state)s (%(sid)s) weather station has been out of communication for 7 days and a work ticket has been created by the NEWA help desk. We are happy to troubleshoot the problem or refer the incident directly to your weather station vendor for quick resolution.</p>
<p>Please reply to this message for assistance or to report the issue as solved.</p>
<p>A third and final notification will be sent at 21 days. Your weather station will be temporarily disabled at that time to prevent inaccurate NEWA model results.<\p>
%(signature)s
</div> </body> </html>
"""
# rem63 20180608 - per Dan Olmstedt - messages are no longer specific to a particular sensor
validation.email.content.station.out_7_days.html['ip-100'] = validation.email.content.station.out_7_days.html.default
validation.email.content.station.out_7_days.html.cellular = validation.email.content.station.out_7_days.html.default
validation.email.content.station.out_7_days.html.ftp = validation.email.content.station.out_7_days.html.default
validation.email.content.station.out_7_days.html.modem = validation.email.content.station.out_7_days.html.default


# rem63 20180608 - per Dan Olmstedt - replace single "missing" message with
#                  separate messages for out_24_hours and day_7 notices.
# TEXT version of 7 day message
validation.email.content.station.out_7_days['text.default'] = """
Your  %(name)s, %(state)s (%(sid)s) weather station has been out of communication for 7 days and a work ticket has been created by the NEWA help desk. We are happy to troubleshoot the problem or refer the incident directly to your weather station vendor for quick resolution.

Please reply to this message for assistance or to report the issue as solved. 

A third and final notification will be sent at 21 days. Your weather station will be temporarily disabled at that time to prevent inaccurate NEWA model results.

%(signature)s
"""
# rem63 20180608 - per Dan Olmstedt - messages are no longer specific to a particular sensor
validation.email.content.station.out_7_days.text['ip-100'] = validation.email.content.station.out_7_days.text.default
validation.email.content.station.out_7_days.text.cellular = validation.email.content.station.out_7_days.text.default
validation.email.content.station.out_7_days.text.ftp = validation.email.content.station.out_7_days.text.default
validation.email.content.station.out_7_days.text.modem = validation.email.content.station.out_7_days.text.default


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for instances when errors occur
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# rem63 20180608 - per Dan Olmstedt
#       error messages always wer e the same for all sensors, however, other
#       requirements for seprate 24 hour and 7 day notices made it necesary
#       to duplicate the error message for each of the time spans
# HTML version of error message
validation.email.content.station.out_24_hours.html.error = """
<html xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>NEWA has not received data from the weather station at %(name)s, %(state)s (%(sid)s) since %(last_time)s.</h3>
<p>However, the following error occurred so we were unable to notify the station contact :</p>
<p>&nbsp;&nbsp;&nbsp;&nbsp;<b>%(error)s</b></p>
%(signature)s
</div> </body> </html>
"""
validation.email.content.station.out_7_days.html.error = validation.email.content.station.out_24_hours.html.error


# rem63 20180608 - per Dan Olmstedt
#       error messages always were the same for all sensors, however, other
#       requirements for separate 24 hour and 7 day notices made it necesary
#       to duplicate the error message for each of the time spans
# TEXT version of error message
validation.email.content.station.out_24_hours.text.error = """
NEWA has not received data from the weather station at %(name)s, %(state)s (%(sid)s) since %(last_time)s.

However, the following error occurred so we were unable to notify the station contact :
    %(error)s

%(signature)s
"""
validation.email.content.station.out_7_days.text.error = validation.email.content.station.out_24_hours.text.error


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for content.summary
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation.email.content.summary.contact = """       Email sent to %(email_sent)s"""

validation.email.content.summary.station = """    %(state)s %(network)s station : %(sid)s : %(name)s"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for content.summary.activate
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation.email.content.summary.activate.detail = """        Began reporting at %(activation_time)s"""

validation.email.content.summary.activate.text = """
NEWA is again receiving data from the following weather station(s) in your network. Please place them on Active Yes status.

%(summary)s

In the Filemaker NEWA metadata record for the station, in the "Active" field click the "Yes" radio button and submit your changes. NEWA metadata is at http://squall.nrcc.cornell.edu:591/fmi/iwp/res/iwp_home.html

If you feel that you received this email in error, please contact Dan Olmstead <dlo6@cornell.edu>, New York State IPM Program.

%(signature)s
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for content.summary.activate
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation.email.content.summary.deactivate.detail = """       All data missing for %(days_missing)d days ... last reported at %(last_time)s"""

validation.email.content.summary.deactivate.text = """
Please place the following weather station(s) in your network on Active Out status.

%(summary)s

NEWA has not received data for three or more weeks. An email advising that the station will be placed on inactive status has been sent to the station contact listed.

In the Filemaker NEWA metadata record for the station, in the "Active" field click the "Out" radio button and submit your changes. NEWA metadata is at http://squall.nrcc.cornell.edu:591/fmi/iwp/res/iwp_home.html

If you feel that you received this email in error, please contact Dan Olmstead <dlo6@cornell.edu>, New York State IPM Program.
%(signature)s
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize details of content for content.summary.missing
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation.email.content.summary.missing.detail = """       All data missing for %(days_missing)d days ... last reported at %(last_time)s"""
validation.email.content.summary.missing.text = """
%(summary)s
"""

