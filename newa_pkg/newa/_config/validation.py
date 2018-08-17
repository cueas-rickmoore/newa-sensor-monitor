
from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize validation configuration
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

validation = ConfigObject('validation',None)
validation.constraints = (('network','!=','icao'),('active','=','Y'))
validation.search_criteria = (('network','!=','icao'),)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize limits for data extremes
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

extremes = ConfigObject('extremes',None)
extremes.stddevs = {
    'invalid' : {'daily_pcpn':10,'dewpt':7,'dewpt_depr':7,'lwet':7,'pcpn':10,
                 'rhum':7,'srad':7,'st4i':7,'st8i':7,'temp':7,'wdir':7,'wspd':7},
    'suspect' : {'daily_pcpn':7,'dewpt':4,'dewpt_depr':4,'lwet':4,'pcpn':7,
                 'rhum':4,'srad':4,'st4i':4,'st8i':4,'temp':4,'wdir':4,'wspd':4},
    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize sequence filters and limits
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sequences = ConfigObject('sequences',None)
sequences.filters = {
    'default' : ( ('x==x', '', 'identical values', str),
                  ('missing', '', 'missing values', 'missing'), ),
    'dewpt' : ( ('x==x', '', 'identical dew point values', lambda x:'%d' % x),
               ('missing', '', 'missing dew point values', 'missing'), ),
    'dewpt_depr' : ( ('x==x', '', 'identical dew point depression values', lambda x:'%d' % x),
               ('missing', '', 'missing dew point depression values', 'missing'), ),
    'lwet' : ( ('x==0', 'if run[0] == 0', 'leaf wetness == 0', '0'),
               ('0<X<60', 'if (run[0] > 0 and run[0] < 60)', '0 < leaf wetness < 60', lambda x:'%d' % x),
               ('x==60', 'if run[0] == 60', 'leaf wetness == 60', '60'),
               ('missing', '', 'missing values for leaf wetness', 'missing'), ),
    'pcpn' : ( ('x==0', 'if run[0] == 0', 'precipitation == 0', '0'),
               ('x>0', 'if run[0] > 0', 'precipitation > 0', lambda x:('%5.2f' % x).strip()),
               ('missing', '', 'missing precipitation values', 'missing'), ),
    'rhum' : ( ('0<x<100', 'if (run[0] > 0 and run[0] < 100)', '0 < humidity < 100', lambda x:'%d' % x),
               ('x==100', 'if run[0] == 100', 'humidity == 100', '100'),
               ('missing', '', 'missing values', 'missing'), ),
    'srad' : ( ('x==0', 'if run[0] == 0', 'surface radiation == 0', '0'),
               ('x>0', 'if run[0] > 0', 'surface radiation > 0', lambda x:('%5.2f' % x).strip()),
               ('missing', '', 'missing surface radiation values', 'missing'), ),
    'temp' : ( ('x==x', '', 'identical temperature values', lambda x:'%d' % x),
               ('missing', '', 'missing temperature values', 'missing'), ),
    'wdir' : ( ('x==x', '', 'identical wind directions', lambda x:'%d' % x),
               ('missing', '', 'missing wind directions values', 'missing'), ),
    'wspd' : ( ('x<5', 'if run[0] < 5', 'wind speed < 5', lambda x:'%d' % x),
               ('5<=x<10', 'if run[0] >= 5 and run[0] < 10', '5 <= wind speed < 10', lambda x:'%d' % x),
               ('x>=10', 'if run[0] >= 10', 'wind speed >= 10', lambda x:'%d' % x),
               ('missing', '', 'missing wind speed values', 'missing'), ),
    'zero' : ( ('x<0', 'if run[0] < 0', 'value < 0', str),
               ('x==0', 'if run[0] == 0', 'value == 0', '0'),
               ('x>0', 'if run[0] > 0', 'value > 0', str),
               ('missing', '', 'missing values', 'missing'), ),
    }
sequences.filters['st4i'] = sequences.filters['temp']
sequences.filters['st8i'] = sequences.filters['temp']

sequences.min_run_lengths = {'dewpt':2,'dewpt_depr':2,'lwet':2,'pcpn':2,
                             'rhum':2,'srad':2,'st4i':2,'st8i':2,'temp':2,
                             'wdir':2,'wspd':2}
sequences.stddevs = {
    'invalid' : {'dewpt':7,'dewpt_depr':7,'lwet':7,'pcpn':7,'rhum':7,'srad':7,
                 'st4i':7,'st8i':7,'temp':7,'wdir':7,'wspd':7},
    'suspect' : {'dewpt':4,'dewpt_depr':4,'lwet':4,'pcpn':4,'rhum':4,'srad':4,
                 'st4i':4,'st8i':4,'temp':4,'wdir':4,'wspd':4},
    }

sequences.log_filename_template = '%d_sequences.log'
sequences.min_count_cuttoff = 2

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize spike filters and limits
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

spikes = ConfigObject('spikes',None)
spikes.filters = {
      'dewpt' : (('x>0', 'if spike != 0', 'dew point spike > 0', str),),
      'dewpt_depr' : (('x>0', 'if spike != 0', 'dew point depression spike > 0', str),),
      'rhum' : (('x>0', 'if spike != 0', 'humidity spike > 0', str),),
      'srad' : (('x>0', 'if spike != 0', 'surface radiation spike > 0', str),),
      'temp' : (('x>0', 'if spike != 0', 'temperature spike > 0', str),),
      'wdir' : (('x>0', 'if spike != 0', 'wind direction spike > 0', str),),
      'wspd' : (('x>0', 'if spike != 0', 'wind speed spike > 0', str),),
     }
spikes.filters['st4i'] = spikes.filters['temp']
spikes.filters['st8i'] = spikes.filters['temp']

spikes.stddevs = {
    'invalid' : {'dewpt':7,'dewpt_depr':7,'lwet':7,'pcpn':10,'rhum':7,'srad':7,
                 'st4i':7,'st8i':7,'temp':7,'wdir':7,'wspd':7},
    'suspect' : {'dewpt':4,'dewpt_depr':4,'lwet':4,'pcpn':7,'rhum':4,'srad':4,
                 'st4i':4,'st8i':4,'temp':4,'wdir':4,'wspd':4},
    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize the validation email configuration
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

email = ConfigObject('email',None,'header','station','sensor')
validation.addChild(email)
validation.email.header.summary = {
           'subject' : 'Summary of network weather stations that did not report on %(report_date)s',
           'sender'  : 'Northeast Regional Climate Center <nrcc@cornell.edu>',
           'mail_to' : 'Keith Eggleston <keith.eggleston@cornell.edu>, Juliet E. Carroll <jec3@cornell.edu>',
           'cc'      : 'Art DeGaetano <atd2@cornell.edu>,',
           'bcc'     : 'Rick Moore <rem63@cornell.edu>',
           'signature' : 'Northeast Regional Climate Center\nCornell University',
           }

validation.email.header.newa = {
           'subject' : 'NEWA Station %(name)s Outage Report for %(report_date)s',
           'sender'  : 'Juliet E. Carroll <jec3@cornell.edu>',
           'mail_to' : '%(name)s <%(email)s>',
           'cc'      : '%(name)s <%(email)s',
           #'cc'      : 'Art DeGaetano <atd2@cornell.edu>,Keith Eggleston <keith.eggleston@cornell.edu>',
           #'bcc'     : 'Rick Moore <rem63@cornell.edu>',
           }
validation.email.header.newa['signature.html'] = "<p>NEWA</br>New York State IPM Program and the Northeast Regional Climate Center</br>Cornell University</p>"
validation.email.header.newa['signature.text'] = "NEWA\nNew York State IPM Program and the Northeast Regional Climate Center\nCornell University"
validation.email.header.newa['tag_line.station'] = 'NEWA has not received data from your weather station at %(name)s since %(last_report)s.'
validation.email.header.newa.tag_line.sensor = 'NEWA has not received data from one or more sensors on your weather station at %(name)s'

validation.email.header.cu_log = validation.email.header.newa.asDict()

validation.email.header.njwx = {
           'subject' : 'NJWX Station %(name)s Outage Report for %(report_date)',
           'sender'  : 'Northeast Regional Climate Center <nrcc@cornell.edu>',
           'mail_to' : '%(name)s <%(email)s>',
           'cc'      : '%(name)s <%(email)s',
           }
validation.email.header.newa['signature.html'] = '<p>Northeast Regional Climate Center</br>Cornell University</p>'
validation.email.header.newa.signature.text = 'Northeast Regional Climate Center\nCornell University'
validation.email.header.njwx['tag_line.station'] = 'Your weather station at %(name)s has not reported data since %(last_report)s.\nPlease take steps to remedy the problem.'
validation.email.header.njwx.tag_line.sensor = 'Your weather station at %(name)s did not report data for one or more sensors.\nPlease take steps to remedy the problem.'

validation.email.header.CT = None
validation.email.header.DE = None
validation.email.header.MA = validation.email.header.newa.asDict()
validation.email.header.NJ = validation.email.header.njwx.asDict()
validation.email.header.NY = validation.email.header.newa.asDict()
validation.email.header.PA = validation.email.header.newa.asDict()
validation.email.header.RI = None
validation.email.header.VT = validation.email.header.newa.asDict()

validation.email.station['IP-100.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<p>If your weather station is down for calibration or routine maintenance, please contact
<a href="mailto:newa@cornell.edu?Subject=Maintenance%%20on%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.
Otherwise, please take steps to remedy the problem.</p>
<p>Make sure the battery in the weather station is good. On WLcom, voltage readings are found at the bottom of the weather information box,
under other weather parameters. Battery voltage readings that drop below 5.9 volts indicate the battery should be replaced.
The replacement 6 volt battery is a Werker WKA6-5F.</p>
<p>Also, please perform the following checks to troubleshoot your IP-100 data connection:</p>
<ol>
<li>Check the physical cabling between the IP-100 and your internet router for damaged or loose connections.</li>
<li>Check whether you have access to the Internet. If necessary, contact your internet service provider for help.</li>
<li>Check whether data from your weather station is being transmitted from your weather station to the IP100 and uploaded to <a href="http://www.rainwise.net">RainwiseNet</a>.
Visit your RainwiseNet webpage.  Once there, verify that the RainwiseNet database for your weather station is up-to-date.
If not, please contact <a href="mailto:Wayne.Burnett@rainwise.com?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(name)s">Wayne Burnett</a>, Rainwise, Inc., for help resolving the issue.</li>
<li>Make sure the Upload Rate is set at 15 minutes on <a href="http://www.rainwise.net">RainwiseNet</a>, under Settings, and Save changes.</li>
</ol>
<p>If the system has been checked and appears to be working, but data is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>, please contact
<a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>, New York State IPM Program.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.station['IP-100.text'] = """
%(tag_line)s

If your weather station is down for calibration or routine maintenance, please send an email to NEWA@cornell.edu with the subject line: "Maintenance on %(sensor)s on the %(network)s network at %(sid)s:%(name)s". Otherwise, please take steps to remedy the problem.

Make sure the battery in the weather station is good. On WLcom, voltage readings are found at the bottom of the weather information box, under other weather parameters. Battery voltage readings that drop below 5.9 volts indicate the battery should be replaced. The replacement 6 volt battery is a Werker WKA6-5F.

Also, please perform the following checks to troubleshoot your IP-100 data connection:

1. Check the physical cabling between the IP-100 and your internet
   router for damaged or loose connections.

2. Check whether you have access to the Internet. If necessary,
   contact your internet service provider for help.

3. Check whether data from your weather station is being transmitted
   from your weather station to the IP100 and uploaded to RainwiseNet
   (http://www.rainwise.net).  Visit your RainwiseNet webpage. Once
   there, verify that the RainwiseNet database for your weather
   station is up-to-date.  If not, please contact Wayne Burnett,
   Rainwise, Inc., for help resolving the issue. Use the email
   address <Wayne.Burnett@rainwise.com>. Also, please use the
   subject line:
      "Issue with %(sensor)s on the %(network)s network at %(name)s"

4. Make sure the Upload Rate is set at 15 minutes on RainwiseNet
   (http://www.rainwise.net), under Settings, and Save changes.

If the system has been checked and appears to be working, but data is still not being displayed on the NEWA website (http://newa.cornell.edu) please contact NEWA@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(name)s"

If you feel that you received this email in error, please contact Juliet E. Carroll, New York State IPM Program at <jec3@cornell.edu> with the subject : "Outage Notification Error received for %(sid)s:%(name)s"

%(signature)s
"""

validation.email.station['ftp.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<p>If your weather station is down for calibration or routine maintenance, please contact
<a href="mailto:newa@cornell.edu?Subject=Maintenance%%20on%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.
Otherwise, please take steps to remedy the problem.</p>
<p>Make sure the battery in the weather station is good.
On WLcom, voltage readings are found at the bottom of the weather information box, under other weather parameters.
Battery voltage readings that drop below 5.9 volts indicate the battery should be replaced. The replacement 6 volt battery is a Werker WKA6-5F.</p>
<p>Also, please perform the following checks to troubleshoot your FTP connection:</p>
<ol>
<li>Check to see if data is being transmitted from your weather station to the computer interface and uploaded into WLcom on your computer.
If not, please contact <a href="mailto:Wayne.Burnett@rainwise.com?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(name)s">Wayne Burnett</a>, Rainwise, Inc., for help resolving the issue.</li>
<li>Make sure the computer is on and the Cornell ftp software is running. <b>Remember:</b> automatic upgrades, power outages, or anything else that causes a computer restart will require <b>manual restart</b> of the Cornell ftp software.</li>
<li>Check the physical cabling between the computer interface and your computer for damaged or loose connections.</li>
<li>Check that the connection between your computer and the internet is active. For hard-wired connections, check the cabling for damaged or loose connections. If necessary, contact your internet service provider for help.</li>
</ol>
<p>If the system has been checked and appears to be working, but data is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>,
please contact <a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>, New York State IPM Program.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.station.ftp.text = """
%(tag_line)s

If your weather station is down for calibration or routine maintenance, please send an email to NEWA@cornell.edu with the subject : "Maintenance on %(sensor)s on the %(network)s network at %(sid)s:%(name)s". Otherwise, please take steps to remedy the problem.

Make sure the battery in the weather station is good. On WLcom, voltage readings are found at the bottom of the weather information box, under other weather parameters. Battery voltage readings that drop below 5.9 volts indicate the battery should be replaced. The replacement 6 volt battery is a Werker WKA6-5F.

Also, please perform the following checks to troubleshoot your FTP connection:

1. Check to see if data is being transmitted from your weather
   station to the computer interface and uploaded into WLcom on
   your computer. If not, please contact Wayne Burnett, Rainwise,
   Inc., for help resolving the issue. Use the email address
   <Wayne.Burnett@rainwise.com>. Also please use the subject line:
      "Issue with %(sensor)s on the %(network)s network at %(name)s"

2. Make sure the computer is on and the Cornell ftp software is
   running. REMEMBER: automatic upgrades, power outages, or
   anything else that causes a computer restart will require
   MANUAL RESTART of the Cornell ftp software.

3. Check the physical cabling between the computer interface and
   your computer for damaged or loose connections.

4. Check that the connection between your computer and the internet
   is active.  For hard-wired connections, check the cabling for
   damaged or loose connections.  If necessary, contact your
   internet service provider for help.

If the system has been checked and appears to be working, but data is still not being displayed on the NEWA website (http://newa.cornell.edu) please contact NEWA@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(name)s"

If you feel that you received this email in error, please contact Juliet E. Carroll, New York State IPM Program at <jec3@cornell.edu> with the subject : "Outage Notification Error received for %(sid)s:%(name)s"
%(signature)s
"""

validation.email.station['hobo.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<p>If your weather station is down for calibration or routine maintenance, please contact <a href="mailto:newa@cornell.edu?Subject=Maintenance%%20on%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a></p>
<p>If you have checked your system and everything appears to be working, but data is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>,
please contact <a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>, New York State IPM Program.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.station.hobo.text = """
%(tag_line)s

If your weather station is down for calibration or routine maintenance, please send an email to NEWA@cornell.edu with the subject line: "Maintenance on %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

If you have checked you system and everything appears to be working, but data is still not being displayed on the NEWA website(http://newa.cornell.edu), please send an email to newa@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(name)s"

If you feel that you received this email in error, please send an email to Juliet E. Carroll <jec3@cornell.edu> with the subject : "Outage Notification Error recieved for 0%(sid)s:%(name)s"

%(signature)s
"""

validation.email.station['modem.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<h4>Sensatronics weather stations are obsolete. Modem connections will no longer be supported as of December 31, 2013.
Please consider obtaining a Rainwise AgroMet (MKIII SP1) weather station for connecting to NEWA.
For details, visit the <a href="http://newa.cornell.edu/index.php?page=get-weather-station">"Get a NEWA Weather Station"</a> web page.</h4>
<p>If your weather station is down for calibration or routine maintenance, please contact 
<a href="mailto:newa@cornell.edu?Subject=Maintenance%%20on%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.
Otherwise, please take steps to remedy the problem.</p>
<p>Make sure the batteries in the weather station are good. If needed, replace the batteries.
Also, please perform the following checks to troubleshoot your modem connection: </p>
<ol>
<li>Check the physical connection between the weather station and the phone modem for damaged or loose cable connections.</li>
<li>If the modem line is on a timer, check to make sure the timer is functioning properly for the timing of the NEWA modem call.</li>
<li>Make sure there is a dial tone on the phone line.</li>
</ol>
<p>If the system has been checked and appears to be working, but data is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>,
please contact <a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>, New York State IPM Program.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.station.modem.text = """
%(tag_line)s

If your weather station is down for calibration or routine maintenance, please send an email to NEWA@cornell.edu with the subject line: "Maintenance on %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

Sensatronics weather stations are obsolete. Modem connections will no longer be supported as of December 31, 2013.  Please consider obtaining a Rainwise AgroMet (MKIII SP1) weather station for connecting to NEWA. 
For details, visit the "Get a NEWA Weather Station" web page (http://newa.cornell.edu/index.php?page=get-weather-station).

Make sure the batteries in the weather station are good. If needed, replace the batteries.

Also, please perform the following checks to troubleshoot your modem connection:

1. Check the physical connection between the weather station and the
   phone modem for damaged or loose cable connections.

2. If the modem line is on a timer, check to make sure the timer is
   functioning properly for the timing of the NEWA modem call.

3. Make sure there is a dial tone on the phone line.

If the system has been checked and appears to be working, but data for the sensor(s) is still not being displayed on the NEWA website (http://newa.cornell.edu) please contact NEWA@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

If you feel that you received this email in error, please contact Juliet E. Carroll, New York State IPM Program at <jec3@cornell.edu> with the subject : "Outage Notification Error received for %(sid)s:%(name)s"

%(signature)s
"""

validation.email.sensor['missing.html'] = "<li>%s sensor did not report : last reported %s</li>"
validation.email.sensor['missing.text'] = "\n    %d. %s sensor did not report : last reported %s"

validation.email.sensor['IP-100.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<p>Please check the following sensor(s) for problems: <ol>
%(sensors_missing)s
</ol>
<p>If the sensor(s) have been checked and appear to be working, but data for the sensor(s) is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>,
please contact <a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20netwok%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.sensor['IP-100.text'] = """
%(tag_line)s

Please check the following sensor(s) for problems:

%(sensors_missing)s

If the sensor(s) has been checked and appears to be working, but data for the sensor(s) is still not being displayed on the NEWA website (http://newa.cornell.edu) please contact NEWA@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

If you feel that you received this email in error, please contact Juliet E. Carroll, New York State IPM Program at <jec3@cornell.edu> with the subject : "Outage Notification Error received for %(sid)s:%(name)s"

%(signature)s
"""

validation.email.sensor['ftp.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<p>Please check the following sensor(s) for problems: <ol>
%(sensors_missing)s
</ol>
<p>If the sensor(s) have been checked and appear to be working, but data for the sensor(s) is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>,
please contact <a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.sensor.ftp.text = """
%(tag_line)s

Please check the following sensor(s) for problems:

%(sensors_missing)s

If the sensor(s) has been checked and appears to be working, but data for the sensor(s) is still not being displayed on the NEWA website (http://newa.cornell.edu) please contact NEWA@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

If you feel that you received this email in error, please contact Juliet E. Carroll, New York State IPM Program at <jec3@cornell.edu> with the subject : "Outage Notification Error received for %(sid)s:%(name)s"

%(signature)s
"""

validation.email.sensor['hobo.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<p>Please check the following sensor(s) for problems: <ol>
%(sensors_missing)s
</ol>
<p>If the sensor(s) have been checked and appear to be working, but data for the sensor(s) is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>,
please contact <a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.sensor.hobo.text = """
%(tag_line)s

Please check the following sensor(s) for problems:

%(sensors_missing)s

If the sensor(s) has been checked and appears to be working, but data for the sensor(s) is still not being displayed on the NEWA website (http://newa.cornell.edu) please contact NEWA@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

If you feel that you received this email in error, please contact Juliet E. Carroll, New York State IPM Program at <jec3@cornell.edu> with the subject : "Outage Notification Error received for %(sid)s:%(name)s"

%(signature)s
"""

validation.email.sensor['modem.html'] = """
<html  xmlns="http://www.w3.org/TR/REC-html40">
<head> <meta http-equiv=Content-Type content="text/html; charset=macintosh"> </head>
<body lang=EN-US link=blue vlink=purple style="tab-interval:.5in"> <div>
<h3>%(tag_line)s</h3>
<h4>Sensatronics weather stations are obsolete. Modem connections will no longer be supported as of December 31, 2013.
Please consider obtaining a Rainwise AgroMet (MKIII SP1) weather station for connecting to NEWA.
For details, visit the <a href="http://newa.cornell.edu/index.php?page=get-weather-station">"Get a NEWA Weather Station"</a> web page.</h4>
<p>Please check the following sensor(s) for problems: <ol>
%(sensors_missing)s
</ol>
<p>If the sensor(s) have been checked and appear to be working, but data for the sensor(s) is still not being displayed on the <a href="http://newa.cornell.edu/">NEWA website</a>,
please contact <a href="mailto:newa@cornell.edu?Subject=Issue%%20with%%20%(sensor)s%%20on%%20the%%20%(network)s%%20network%%20at%%20%(sid)s:%(name)s">NEWA@cornell.edu</a>.</p>
<p><b>If you feel that you received this email in error, please contact <a href="jec3@cornell.edu?Subject=Outage%%20Notification%%20Error%%20recieved%%20for%%20%(sid)s:%(name)s">Juliet E. Carroll</a>.</b></p>
%(signature)s
</div> </body> </html>
"""

validation.email.sensor.modem.text = """
%(tag_line)s

Sensatronics weather stations are obsolete. Modem connections will no longer be supported as of December 31, 2013. Please consider obtaining a Rainwise AgroMet (MKIII SP1) weather station for connecting to NEWA. For details, visit the "Get a NEWA Weather Station" web page (http://newa.cornell.edu/index.php?page=get-weather-station).

Please check the following sensor(s) for problems:

%(sensors_missing)s

If the sensor(s) has been checked and appears to be working, but data for the sensor(s) is still not being displayed on the NEWA website (http://newa.cornell.edu) please contact NEWA@cornell.edu with the subject : "Issue with %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

If you feel that you received this email in error, please contact Juliet E. Carroll, New York State IPM Program at <jec3@cornell.edu> with the subject : "Outage Notification Error received for %(sid)s:%(name)s"

!!!!! Modems will no longer be supported as of December 31, 2013 !!!!!
For help finding a new method for uploading your data send an email to NEWA@cornell.edu with the subject : "Replace modem for %(sensor)s on the %(network)s network at %(sid)s:%(name)s"

%(signature)s
"""

