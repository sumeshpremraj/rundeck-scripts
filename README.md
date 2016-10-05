Collection of custom scripts for Rundeck.

* **rundeck-healthcheck.sh**: This script checks the health of peers in a cluster, and takes over jobs if the other node is down
* **summary-report.py**: This script parses Rundeck execution logs, and sends out a summary email of all failures since the last time this script was executed

The scripts require some editing. The user-editable lines are placed near the top, and well commented.

As always, pull requests are welcome :)
