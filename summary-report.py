#!/usr/bin/env python
"""
    Script to parse Rundeck execution log and
    send a summary email with all job failures

    This script uses pygtail to tail logs
    Run this script as a cron at whatever interval you desire
    (the mail text is written expecting 3 hour interval, you can edit that)
"""
#To the arguments handling
import sys
import getopt
import socket
import smtplib
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

def addLog(log_message):  
  global loggerName
  var = "{}-{}\n".format(str(datetime.now())[:-7],log_message)
  with open("summary-report.log", "a") as myfile:
      myfile.write(var)
  return

addLog("Starting script")

try:
  opts, args = getopt.getopt(sys.argv[1:],"hh:p:f:t:s:b:g:",["help="])
except getopt.GetoptError:
  print 'Try to use the help with the following command: summary-report.py -h'
  sys.exit(2)

for opt,arg in opts:
  if opt == '-h':
    print """summary-report.py has the following arguments options:
      -p <production>
      -t <recipients emails>
      -s <smtp host/sender email>
      -b <base url>
    """
    sys.exit()
  elif opt == "-p":
    PROJECT = arg
  elif opt == "-t":
    rcv = arg
  elif opt == "-s":
    smtp_username = arg
  elif opt == "-b":
    BASE_URL = arg
  elif opt == "-g":
    try:
      smtp_port = int(arg)
    except ValueError:
      print("Option '-g' needs an integer as argument.")
      sys.exit()

LOG = "/var/log/rundeck/rundeck.executions.log"
fail_count = 0

msg = MIMEMultipart('alternative')
msg['From'] = smtp_username
msg['To'] = ", ".join(rcv)

jobs = ''

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
        failed_jobs.append(
            JOB(job_date, LINK(execution_id), execution_id, job_name))

# Send mail only if there are failures;
# Remove this if conditional to send mail always
if fail_count > 0:
  addLog("Total jobs failed are {}".format(fail_count))
  msg['Subject'] = 'Rundeck summary: ' + str(fail_count) + ' jobs failed'
  part1 = MIMEText(mail_text, 'plain')
  part2 = MIMEText(mail_text, 'html')
  msg.attach(part1)
  msg.attach(part2)
  port_list = [587, 465, 25]
  flag = True
  index=0
  while flag:
    try:
      server = smtplib.SMTP(smtp_server, port_list[index])
      server.starttls()
      server.login(smtp_username, smtp_password)
      server.sendmail(sender, rcv, msg.as_string())
      server.quit()
      flag=False
    except :
      index+=1
else :
  addLog("No job failed")
addLog("Quitting the script")
