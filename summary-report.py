#!/usr/bin/env python
"""
    Script to parse Rundeck execution log and
    send a summary email with all job failures

    This script uses pygtail to tail logs
    Run this script as a cron at whatever interval you desire
    (the mail text is written expecting 3 hour interval, you can edit that)
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import repeat
from smtplib import SMTP

from pygtail import Pygtail

###############################################################################
# User editable variables BEGIN
###############################################################################

# Name of the Rundeck project for which you want reports, usually Production
PROJECT = 'Production'

# The data-from user for email, ie. what the recipient sees in an email client
SENDER = 'rundeck-reports@domain.com'

# Recipients for the summary email
RCV = ['team-devops@domain.com', 'team-devs@domain.com']

# SMTP server to send mails from
SMTP_SERVER = 'mail.domain.com'

# SMTP authentication username:
#   this can be different from the data-from specified above
SMTP_USERNAME = 'system-reports@domain.com'

# SMTP authentication password
SMTP_PASSWORD = 'goodstrongpassword'

# SMTP port
SMTP_PORT = 587

# This will be used in the job execution links in summary email,
# this can be IP or hostname
BASE_URL = 'https://rundeck.internal.domain.tld'

###############################################################################
# User editable variables END
###############################################################################

ERROR_MSGS = ('failed]', 'timedout]')
NBSP = '&nbsp;'
JOB = '{{}} {}<a href="{{}}">{{}}</a> {} {{}}<br/>'.format(
    ' '.join(repeat(NBSP, 3)), ' '.join(repeat(NBSP, 9))).format
LINK = '{}/project/{}/execution/show/{{}}'.format(BASE_URL, PROJECT).format
LOG = '/var/log/rundeck/rundeck.executions.log'

msg = MIMEMultipart('alternative')
msg['From'] = SENDER
msg['To'] = ', '.join(RCV)

failed_jobs = []
for line in Pygtail(LOG):
    status = line.split()[4]

    # Look for jobs that failed after retries, or timed out
    # This will exclude jobs that succeed after a retry
    if any(err_msg in status for err_msg in ERROR_MSGS):
        job_date = '{} {}'.format(line.split()[0].strip('['),
                                  line.split()[1].strip(']').split(',')[0])
        job_name = ' '.join(line.split()[7:]).split('"')[1].strip('-/')
        execution_id = status.split(':')[0].strip('[')
        link = LINK(execution_id)
        failed_jobs.append(JOB(job_date, link, execution_id, job_name))

# Send mail only if there are failures;
# Remove this if conditional to send mail always
if failed_jobs:
    mail_text = (
        'List of jobs that failed in the last 3 hours (click on the executi'
        'on ID below to view details of the failed job):<br/><p><strong>Tim'
        'e {} Execution ID {} Job name</strong></p>{}'
    ).format(' '.join(repeat(NBSP, 15)),
             ' '.join(repeat(NBSP, 3)),
             ''.join(failed_jobs))

    msg['Subject'] = 'Rundeck summary: {} jobs failed'.format(len(failed_jobs))
    part1 = MIMEText(mail_text, 'plain')
    part2 = MIMEText(mail_text, 'html')
    msg.attach(part1)
    msg.attach(part2)

    server = SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(SENDER, RCV, msg.as_string())
    server.quit()
