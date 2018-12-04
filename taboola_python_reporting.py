from pytaboola import TaboolaClient
from pytaboola.services import CampaignService, CampaignSummaryReport, AccountService
import datetime
import csv
import pandas as pd
import numpy as np
import pygsheets
import logging

# logging.basicConfig(level=logging.DEBUG, format='%(message)s') #For the logging to display everything not only warning messages used for debug

CLIENT_ID = "YOUR_CLIENT_ID" #from Taboola
CLIENT_SECRET = "YOUR_CLIENT_SECRET" #from Taboola

def create_client(CLIENT_ID, CLIENT_SECRET):
	#Creates Taboola Client object with the given ID and secret.
	client = TaboolaClient(CLIENT_ID, client_secret=CLIENT_SECRET)
	return client

def get_account_names_and_ids(client):
	#Using AccountService to list all the accounts, then returning a list of dicts of the account names and ids respectively
	service = AccountService(client)
	accounts = service.list()
	account_names_ids = []
	for item in accounts["results"]:
		account_names_ids.append({"name": item["name"], "account_id": item["account_id"]})
	return account_names_ids

def print_account_names_and_ids(client):
	#Gets all account names and IDs and prints them out with a number attached for easier reference. Used in main() to print IDs to choose from.
	account_names_ids = get_account_names_and_ids(client)
	count = 1
	print(f"{len(account_names_ids)} accounts found:")
	for account in account_names_ids:
		print(f"{count} : {account['name']}")
		count += 1
	return account_names_ids


def get_campaigns_of_account(client, account_id):
	#Using CampaignService to list all campaigns in a given account then returning a list of dicts of the campaign names and ids respectively
	service = CampaignService(client,account_id)
	campaigns = service.list()
	campaign_names_ids = []
	for item in campaigns:
		campaign_names_ids.append({"name": item["name"], "id": item["id"]})
	return campaign_names_ids


def get_campaign_ids_containing_str(client, account_id, string):
	#Gets campaign IDs of account BUT ONLY IF campaing name contains given string (case insensitive)
	campaigns = [i["id"] for i in get_campaigns_of_account(client,account_id) if string.lower() in i["name"].lower()]
	logging.info(f"{len(campaigns)} matching campaign IDs found.")
	return campaigns


def campaign_report(client, account_id, campaign_id, start_date, end_date):
	#Using CampaignSummaryReport then using its instance's fetch method to fetch a report in the given dimension, start and end date
	service = CampaignSummaryReport(client,account_id)
	try:
		start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d") #Dates have to be a date objects, for which we are using the datetime module
		end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
		dimension = "day" #allowed: day, week, month, etc...
		report = service.fetch(dimension,start_date,end_date,campaign=campaign_id) 	#Report **kwargs allows to set filters eg campaign, platform, country, site, partner_name
		return report
	except ValueError:
		return None 


def create_csv(filename):
	#Creates a new CSV file with only the set headers and no data
	#Needs to be separated from write_to_csv to avoid writing multiple headers because of the for loop for the multiple campaigns
	date_time = datetime.datetime.now().strftime("%Y-%m-%d__%H_%M_%S") 	#To append chosen name and the current date to the csv file name
	filename = f"Taboola_{filename}_{date_time}.csv"
	with open(filename, "w") as csvfile:
		fieldnames = ["date", "impressions", "clicks", "costs USD", "costs EUR", "conversions"]  #Can be changed according to what is needed
		writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
		writer.writeheader()
	return filename #Used to reference to this filename in other functions
	logging.info(f".csv file created with name {filename}")


def write_to_csv(report, filename):
	with open(filename, "a") as csvfile:
		# fieldnames = [i for i in report["results"][0].keys()]       --> this would be useful if you need all fields which are in the report results
		fieldnames = ["date", "impressions", "clicks", "costs USD", "costs EUR", "conversions"]  	#Fieldnames here are named the same way as the dictionary items in the results of the report
		writer = csv.DictWriter(csvfile,fieldnames=fieldnames)
		for dictionary in report["results"]: #Report is returned by campaign_report, which is a multi-level dict object. We only need results dict from that.
			writer.writerow(
				#The rows below which are commented out are for writing other data (If you do that make sure to include them in the fieldnames above as well!!)
				{"date": dictionary["date"],
				# "date_end_period": dictionary["date_end_period"],
				"impressions": dictionary["impressions"],
				"clicks": dictionary["clicks"],
				"costs USD": dictionary["spent"],
				# "conversions_value": dictionary["conversions_value"],
				# "roas": dictionary["roas"],
				# "ctr": dictionary["ctr"],
				# "cpm": dictionary["cpm"],
				# "cpc": dictionary["cpc"],
				# "campaigns_num": dictionary["campaigns_num"],
				# "cpa": dictionary["cpa"],
				# "cpa_clicks": dictionary["cpa_clicks"],
				# "cpa_views": dictionary["cpa_views"],
				"conversions": dictionary["cpa_actions_num"],
				# "cpa_actions_num_from_clicks": dictionary["cpa_actions_num_from_clicks"],
				# "cpa_actions_num_from_views": dictionary["cpa_actions_num_from_views"],
				# "cpa_conversion_rate": dictionary["cpa_conversion_rate"],
				# "cpa_conversion_rate_clicks": dictionary["cpa_conversion_rate_clicks"],
				# "cpa_conversion_rate_views": dictionary["cpa_conversion_rate_views"],
				# "currency": dictionary["currency"]
				}
				)

def create_report(client, account_id, string, start_date, end_date, filename):
	#To create the whole csv report with the header rows (create_csv) and the data (write_to_csv).
	#It generates a list of campaign IDs that contain a given string, then for each of those IDs, appends the data (for the given date range) to the csv file created
	#It causes duplicate date rows --> cannot sum rows for the same date (thats done by pandas_pivot)
	logging.info("Getting campaign IDs...")
	campaign_ids = get_campaign_ids_containing_str(client, account_id, string)
	if len(campaign_ids) != 0: #Let's not create a csv file and write to it if there are no matching campaign ID's.
		logging.info("Creating .csv file...")
		filename = create_csv(filename)
		logging.info("Success!")
		for campaign_id in campaign_ids:
			logging.info(f"Writing report from campaign ID {campaign_id} to .csv file ...")
			report = campaign_report(client, account_id, campaign_id, start_date, end_date)
			if report != None:
				if len(report["results"]) != 0: 	#If there is no data for a given campaign ID in the given date range, the returned results list is empty, and we don't want to call write_to_csv in those cases
					write_to_csv(report, filename)
					logging.info("Success!")
				else:
					logging.info(f"The campaign is empty for the given date range, skipping.")
			else:
				logging.info("Report couldn't be fetched because date range is invalid. No file is created.")
	else:
		logging.info("No campaigns found with the given campaign name. No file is created.")
		return None
	return filename 	#Used to reference to this filename in other functions

def pandas_pivot(filename):
	#Used to import a csv file to a pandas data frame, so the data can be pivoted and aggregated by date
	if filename == None:
		raise FileNotFoundError("File is not found.")
	else:
		logging.info("Reading .csv and writing to .xlsx file...")
		cols_to_use = ["impressions", "clicks", "costs USD", "costs EUR", "conversions"]
		pandas_csv = pd.read_csv(filename)
		pandas_pivot = pd.pivot_table(pandas_csv,index="date",aggfunc=np.sum).reindex(cols_to_use, axis=1) #Data frame is stored in a dict which is unordered, reindex is needed to display the columns in the desired order
		filename = (f"{filename}_pivot.xlsx") #To distinguish the name from the .csv file.
		writer = pd.ExcelWriter(filename)
		pandas_pivot.to_excel(writer,"Sheet1")
		writer.save()
		logging.info("Success!")
	return filename

# def write_to_gsheet(dataframe):
# 	#Write pandas dataframe to a Google sheets file
# 	gc = pygsheets.authorize(service_file='creds.json') #creds.json generated with the help of the gSheets API
# 	sheet = gc.open("TEST")
# 	worksheet = sheet[0]
# 	worksheet.set_dataframe(dataframe,(1,1))


def main(): #Main function to ask questions in the command line and run the reporting
	logging.info("Connecting to Taboola API...")
	client = create_client(CLIENT_ID,CLIENT_SECRET)
	logging.info("Getting accounts...")
	account_names_ids = print_account_names_and_ids(client)
	while True:
		choice = input("Which account do you want to report on? (choose a number from above) >>> ")
		try:
			choice_int = int(choice) - 1 #Because of Python ID handling, 1st account is actually choice[0]
			if choice_int in range(len(account_names_ids)): #Choice must be a number between 1 and x where x is the number of accounts. 
				break
			else: 
				print(f"You must choose a number in the range 1-{len(account_names_ids)}!")
		except ValueError: #If the input can't be converted to an int
			print("You must input a number only!")
	account_id = account_names_ids[choice_int]["account_id"]
	string = input("Which campaigns do you want to include? >>> ")
	while True:
		date_from = input("From which date? Use the format 'YYYY-MM-DD please. >>> ")
		try:
			datetime.datetime.strptime(date_from, "%Y-%m-%d") #Input string will only be converted if the user gives the correct format...
			break
		except ValueError:
			print("Please input the date in the correct format!") #... else it keeps asking for the correct format.
	while True:
		date_to = input("To which date? Use the format 'YYYY-MM-DD please. >>> ")
		try:
			datetime.datetime.strptime(date_to, "%Y-%m-%d")
			break
		except ValueError:
			print("Please input the date in the correct format!")
	filename = input("What should be the filename? >>> ")
	report_file = create_report(client, account_id, string, date_from, date_to, filename)
	try:
		pivot = pandas_pivot(report_file)
		logging.info(f"All done! Your report file is ready, named {pivot}")
	except FileNotFoundError:
		return None


main()
