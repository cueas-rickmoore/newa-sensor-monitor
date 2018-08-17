
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.mailers import SmtpMailer, SmtpHtmlMailer
from rccpy.utils.options import stringToTuple
from rccpy.utils.timeutils import dateAsInt, dateAsTuple, asDatetime

from newa.ucan import HourlyDataConnection

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.validation.config import validation as VALIDATION

ONE_DAY = relativedelta(days=1)

STATION_EMAIL_SENT = '        Notification sent to : %(email_sent)s'
TWNETY_FOUR_HOURS = set(range(24))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ValidationManager(object):

    def __init__(self, decisionTree, start_time, end_time, networks,
                       state_coordinators, smtp_host, reportable_datasets,
                       active_status_column, last_report_column, sids_column,
                       debug=False, test_run=False, detail=False,
                       send_emails=True):

        self.decisionTree = decisionTree
        self.start_time = start_time
        self.end_time = end_time
        self.networks = networks
        self.state_coordinators = state_coordinators
        self.smtp_host = smtp_host
        self.reportable_datasets = reportable_datasets
        self.active_status_column = active_status_column
        self.active_status_changes = 0
        self.last_report_column = last_report_column
        self.last_report_updated = False
        self.sids_column = sids_column

        self.mailer = SmtpHtmlMailer(smtp_host)
        self.report_date = self._formatDate(end_time, False)

        self.debug = debug
        self.detail = detail
        self.send_emails = send_emails
        self.test_run = test_run

        self.activations_by_network = defaultdict(list)
        self.activations_by_state = defaultdict(list)
        self.missing_by_network = defaultdict(list)
        self.deactivations_by_network = defaultdict(list)
        self.deactivations_by_state = defaultdict(list)
        self.deactivation_past_due = [ ]

        self.headers = VALIDATION.email.header
        self.station_templates = VALIDATION.email.content.station
        self.summary_templates = VALIDATION.email.content.summary

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def validate(self, station):
        debug = self.debug
        detail = self.detail

        if not station['active'] in ('Y','O'): return None

        station['index'] = N.where(self.sids_column == station['sid'])[0]
        station_info = '%(ucanid)d : %(sid)s : %(name)s' % station
        if debug and detail:
            print '\n***** processing', station_info
        elif self.test_run: print 'processing', station_info

        reportable_datasets = \
            [ name for name in stringToTuple(station['datasets'])
              if name in self.reportable_datasets ]
        reportable_datasets.sort()
        num_datasets = len(reportable_datasets)
        if debug and detail:
            print 'reportable datasets', num_datasets, reportable_datasets

        # look for datasets with missing data
        missing_data = [ ]
        last_valid_hour = -1
        valid_hour_set = set()

        # make connection to UCAN server
        connection = HourlyDataConnection(2, first_hour_in_day=1)
        for dataset_name in reportable_datasets:

            try:
                first_hour, last_hour, data = \
                connection.getData(station, dataset_name, self.start_time,
                                   self.end_time, detail)
            except Exception as e:
                print '\n\n%s' % '\n'.join(e.args)
                if "UnknownUcanId" in e.__class__.__name__:
                    print '\n'
                    break
                else: continue

            if debug and detail:
                print '\n', first_hour, last_hour, len(N.where(N.isfinite(data))[0])
                print data

            if len(data) > 0:
                valid_hours = N.where(N.isfinite(data))[0]
                if len(valid_hours) > 0:
                    valid_hour_set |= set(valid_hours)
                else: missing_data.append(dataset_name)
            else: missing_data.append(dataset_name)

        station['reportable_datasets'] = reportable_datasets
        station['missing_datasets'] = missing_data
        station['valid_hours'] = valid_hour_set
        kwargs = { 'debug' : debug, 'reportable_data' : reportable_datasets }

        return self.decisionTree(self, station, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    # rem63 20180608 - per Dan Olmstead - separate messages for each time span
    #def allMissing(self, station, num_days):
    #    station = self._trackMissing(station, num_days)
    #    station, _email = self._sendStationEmail('daily', station)
    #    return station, _email

    # rem63 20180608 - per Dan Olmstead - separate messages for each time span
    def allMissing(self, station, msg_key, num_days):
        station = self._trackMissing(station, num_days)
        station, _email = self._sendStationEmail(msg_key, station)
        return station, _email

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def activate(self, station):
        print 'activate', station['name'], station['last_report']
        print station['valid_hours']
        self.active_status_column[station['index']] = 'Y'
        self.active_status_changes += 1
        station = self.updateLastReport(station)

        activation_hour = min(list(station['valid_hours']))
        station['activation_time'] = self.start_time + \
                                     relativedelta(hours=activation_hour)
        #station, _email = self._sendStationEmail('activate', station)
        _email = None

        self.activations_by_network[station['network']].append(station)
        self.activations_by_state[station['state']].append(station)

        return station, _email

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deactivate(self, station, num_days, notify_station=False):
        if self.debug: print 'deactivate', station['name'], num_days

        self.active_status_column[station['index']] = 'O'
        self.active_status_changes += 1

        station['days_missing'] = num_days
        station['last_time'] = self._formatDate(station['last_report'],True)

        self.deactivations_by_network[station['network']].append(station)
        self.deactivations_by_state[station['state']].append(station)
        
        if notify_station:
            return self._sendStationEmail('deactivate', station)
        else: return station, None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ignore(self, station):
        return station, None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def pastDue(self, station, num_days):
        station['days_missing'] = num_days
        station['last_time'] = self._formatDate(station['last_report'],True)
        self.deactivation_past_due.append(station)
        return station, None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def reportValidationResults(self, log_filepath):
        debug =  self.debug | self.test_run
        log_file = None
        if self.activations_by_state.keys():
            log_file = open(log_filepath, 'w')
            summary = self._logNetworkResults(log_file, 'activate',
                                              self.activations_by_network)
            #self._notifyStateCoordinators('activate', self.activations_by_state)
        else: summary = ''

        if debug:
            for key in self.deactivations_by_network:
                for station in self.deactivations_by_network[key]:
                    print '\ndeactivate'
                    print station

        if self.deactivations_by_state.keys():
            if log_file is None: log_file = open(log_filepath, 'w')
            else:
                log_file.write('\n')
                summary += '\n'
            logged = self._logNetworkResults(log_file, 'deactivate',
                                             self.deactivations_by_network)
            if debug: print logged
            summary += logged
            #self._notifyStateCoordinators('deactivate',
            #                              self.deactivations_by_state)

        if debug:
            for key in self.missing_by_network:
                for station in  self.missing_by_network[key]:
                    print '\nmissing'
                    print station

        if self.missing_by_network.keys():
            if log_file is None: log_file = open(log_filepath, 'w')
            else:
                log_file.write('\n')
                summary += '\n'
            logged =self._logNetworkResults(log_file, 'missing',
                                            self.missing_by_network)
            if debug: print logged
            summary += logged

        admin_actions = self._sendActionEmail()
        if admin_actions:
            if log_file is None: log_file = open(log_filepath, 'w')
            else: log_file.write('\n')
            log_file.write(admin_actions)
            if debug: print admin_actions

        if log_file is not None: log_file.close()

        print 'summary email content'
        print summary
        return self._sendSummaryEmail('missing', summary, header_key='summary',
                                      report_date=self.report_date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def shutDown(self):
        self.mailer.stop()

        del self.activations_by_network
        del self.activations_by_state
        del self.missing_by_network
        del self.deactivations_by_network
        del self.deactivations_by_state

        del self.active_status_column
        del self.last_report_column

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        
    def trackMissing(self,station, num_days):
        station = self._trackMissing(station, num_days)
        return station, None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateDatabase(self, db_manager):
        db_manager.openFile(mode='a')
        db_manager.updateDataset('last_report', self.last_report_column)
        if self.active_status_changes > 0:
            db_manager.updateDataset('active', self.active_status_column)
        db_manager.closeFile()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateLastReport(self, station):
        valid_hours = station['valid_hours']
        if len(valid_hours) > 0:
            last_hour = max(valid_hours)
            last_hour = self.start_time + relativedelta(hours=last_hour)
            last_report = dateAsInt(last_hour, True)
            self.last_report_column[station['index']] = last_report
            station['last_report'] = last_report
        return station

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _contactAvailable(self, station):
        return 'contact' in station and len(station['contact']) > 0 \
               and 'email' in station and len(station['email']) > 0

    def _getEmailHeader(self, header_key, contacts_etc):
        error = None
        header_tmpls = self.headers[header_key].asDict()
        if self.test_run:
            header_tmpls.update(self.headers['test'].asDict())
        elif self.debug:
            header_tmpls.update(self.headers['debug'].asDict())
        elif 'contact' in header_tmpls['mail_to'] and not \
             self._contactAvailable(contacts_etc):
            header_tmpls = self.headers['error'].asDict()
            errmsg = '       No contact information available for station at %(name)s, %(state)s'
            error = errmsg % contacts_etc

        header = { 'subject'   : header_tmpls['subject'] % contacts_etc,
                   'sender'    : header_tmpls['sender'] % contacts_etc,
                   'mail_to'   : header_tmpls['mail_to'] % contacts_etc,
                   'signature' : header_tmpls['signature'],
                   'cc'        : None,
                   'bcc'       : None,
                   }
        if 'title' in header_tmpls:
            header['title'] = header_tmpls['title'] 
        if error is not None: header['ERROR'] = error

        cc = header_tmpls.get('cc',None)
        if cc is not None:
            if '%(bcontact)s' in cc:
                bcontact = contacts_etc.get('bcontact', None)
                bemail = contacts_etc.get('bemail', None)
                if bcontact and bemail: header['cc'] = cc % contacts_etc
            else: header['cc'] = cc

        bcc = header_tmpls.get('bcc',None)
        if bcc is not None: header['bcc'] = bcc % contacts_etc
        
        return header

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _formatDate(self, date, include_hour):
        date_time = asDatetime(date, True)
        if include_hour: return date_time.strftime('%I %p on %b %d, %Y')
        return date_time.strftime('%b %d, %Y')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _logNetworkResults(self, log_file, status_key, network_dict):
        contact_tmpl = self.summary_templates.contact
        station_tmpl = self.summary_templates.station
        detail_tmpl = self.summary_templates[status_key].detail
        title = self.headers[status_key].title
        log_file.write('\n%s' % title)
 
        # write errors to the log file and accumulate text for the
        # summary email message
        summary_text = title

        for network in self.networks:
            if network not in network_dict: continue
            network_upper = network.upper()
            for station in network_dict[network]:
                station['network'] = network_upper
                message = '\n\n%s' % (station_tmpl % station)
                log_file.write(message)
                summary_text += message

                message = '\n%s' % (detail_tmpl % station)
                log_file.write(message)
                summary_text += message

                if 'error' in station:
                    message = '\n%s' % station['error']
                    summary_text += message
                if 'email_sent' in station:
                    message = '\n%s' % (contact_tmpl % station)
                    log_file.write(message)
                    summary_text += message

        return summary_text

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


    def _notifyStateCoordinators(self, status_key, state_dict):
        state_coordinators = self.state_coordinators
        
        summary_templates = self.summary_templates
        contact_tmpl = summary_templates.contact
        station_tmpl = summary_templates.station
        detail_tmpl = summary_templates[status_key].detail

        for state in state_dict:
            summary_text = ''
            for station in state_dict[state]:
                message = [ station_tmpl % station,
                            detail_tmpl % station ]
                if 'email_sent' in station:
                    message.append(contact_tmpl % station)
                message = '\n%s' % '\n'.join(message)
                summary_text = '%s%s' % (summary_text, message)

            if summary_text:
                self._sendSummaryEmail(status_key, summary_text,
                                       **state_coordinators[state])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _sendActionEmail(self):
        debug = self.debug | self.test_run

        summary = ""
        station_tmpl = '\n\n' + self.summary_templates.station

        active = [ ] 
        for key in self.activations_by_network:
            active.extend(self.activations_by_network[key])

        if len(active) > 0:
            summary += '\n\nThe status of the following station(s) need to be set to "Yes" :'
            detail_tmpl = '\n' + self.summary_templates.activate.detail
            for station in active:
                summary += station_tmpl % station
                summary += detail_tmpl % station
        del active

        inactive = [ ]
        for key in self.deactivations_by_network:
            inactive.extend(self.deactivations_by_network[key])

        if len(inactive) > 0:
            if summary: summary += '\n'
            summary += '\n\nThe status of the following station(s) need to be set to "Out" :'
            detail_tmpl = '\n' + self.summary_templates.deactivate.detail
            for station in inactive:
                summary += station_tmpl % station
                summary += detail_tmpl % station
        del inactive
        
        if len(self.deactivation_past_due) > 0:
            if summary: summary += '\n'
            summary += '\n\nDeactivation past due, the following station(s) urgently need to be set to "Out":'
            detail_tmpl = '\n' + self.summary_templates.deactivate.detail
            for station in  self.deactivation_past_due:
                summary += station_tmpl % station
                summary += detail_tmpl % station

        if len(summary) > 0:
            if debug: print '\n', summary
            header = self._getEmailHeader('action_required', { })
            if debug: print 'email header :', header
            # use a temporary text mailer
            mailer = SmtpMailer(self.smtp_host)
            mailer.sendMessage(header['sender'], header['mail_to'], 
                               header['subject'], summary, cc=header['cc'],
                               bcc=header['bcc'], debug=self.detail)
            mailer.stop()
            del mailer
            return summary
        else:
            if debug: print '\nno adminstrative action required'
            return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _sendStationEmail(self, status_key, station):
        debug = self.debug or self.test_run
        templates = self.station_templates[status_key]

        station['report_date'] = self.report_date

        header = self._getEmailHeader(status_key, station)
        if 'ERROR' in header:
            templ_key = 'error'
            station['error'] = header['ERROR']
            del header['ERROR']
        else: templ_key = station['uplink'].lower()
        station['signature'] = header['signature']

        templ = templates.text.get(templ_key, templates.text.default)
        text = templ % station

        station['signature'] = header['signature'].replace('\n','</br>')
        templ = templates.html.get(templ_key, templates.html.default)
        html = templ % station

        _email  = self.mailer.sendMessage(header['sender'], header['mail_to'],
                                          header['subject'], html, text=text,
                                          cc=header['cc'], bcc=header['bcc'], 
                                          test=self.test_run, debug=self.detail)

        del station['signature']
        error = station.get('error',None)
        if _email is not None:
            station['email_sent'] = header['mail_to']
            if debug:
                print '\nemail sent to', _email['To']
                print header['subject']
                if 'error' is not None: print error
        elif debug:
            print '\nemail would be sent to', header['mail_to']
            print header['subject']
            if 'error' is not None: print error

        return station, _email

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _sendSummaryEmail(self, status_key, summary, **kwargs):
        if 'header_key' in kwargs:
            header = self._getEmailHeader(kwargs['header_key'], kwargs)
        else: header = self._getEmailHeader(status_key, kwargs)

        header['summary'] = summary
        text = self.summary_templates[status_key].text % header

        # use a temporary text mailer
        mailer = SmtpMailer(self.smtp_host)
        _email  = mailer.sendMessage(header['sender'], header['mail_to'], 
                                     header['subject'], text, cc=header['cc'],
                                     bcc=header['bcc'], debug=self.detail)
        mailer.stop()
        del mailer

        return _email

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _trackMissing(self, station, num_days):
        station['days_missing'] = num_days
        station['last_time'] = self._formatDate(station['last_report'],True)
        if self.debug:
            message = '%(days_missing)4d days ago : %(active)s : %(name)s (%(sid)s) last reported on %(last_time)s'
            print message % station
        self.missing_by_network[station['network']].append(station)
        return station

