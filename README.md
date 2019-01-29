# TaboolaReporting
A simple Taboola reporting "interface" using pytaboola - and my first ever git repo

### Project description:
A command-line interface coded in Python3 that is streamlining the download of daily reports. The problem is that the online Taboola interface only allows daily reports to be downloaded aggregated, and not filtered by campaign. This script gives a nice export filtered per campaign for an easy overview and further analysis. Uses [https://github.com/dolead/pytaboola] for the Taboola client. 

### Usage:
`$ python3 taboola_python_reporting.py `, then follow the instructions in the terminal

### Functions: 
- fetch Taboola accounts using API key
- command-line user input about account, campaign name filter and date range
- create a .csv and .xlsx report with the given conditions

### Note:
Please note that this is my first ever commit to github, and as a newbie in programming altogether, having been only learned python for around 2 months, my code is definitely not flawless. It works, it saves a lot of time for me, so I thought I would share it. If you find anything that could be made better, please tell me, that is how I'll learn!
