import pandas as pd
import numpy
import xlrd
from collections import OrderedDict
import json
from datetime import datetime, timedelta
import os
import re
import operator
import logging

us_state_abbrev = {
    'AL': 'Alabama',
    'AK': 'Alaska',
    'AZ': 'Arizona',
    'AR': 'Arkansas',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'IA': 'Iowa',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'ME': 'Maine',
    'MD': 'Maryland',
    'MA': 'Massachusetts',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MS': 'Mississippi',
    'MO': 'Missouri',
    'MT': 'Montana',
    'NE': 'Nebraska',
    'NV': 'Nevada',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NY': 'New York',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VT': 'Vermont',
    'VA': 'Virginia',
    'WA': 'Washington',
    'WV': 'West Virginia',
    'WI': 'Wisconsin',
    'WY': 'Wyoming',
}

canada_state_abbrev = {
  "AB": "Alberta",
  "BC": "British Columbia",
  "MB": "Manitoba",
  "NB": "New Brunswick",
  "NL": "Newfoundland and Labrador",
  "NS": "Nova Scotia",
  "NT": "Northwest Territories",
  "NU": "Nunavut",
  "ON": "Ontario",
  "PE": "Prince Edward Island",
  "QC": "Québec",
  "SK": "Saskatchewan",
  "YT": "Yukon"
}

China = {'China':'Mainland China'}

headers = {'Country':'Country/Region', 'Confirmed': 'Total Comfirmed', 'Deaths': 'Total Deaths','Recovered': 'Total Recovered','Demised': 'Total Deaths'}
allow_headers = ['Province/State','Country/Region','Total Comfirmed','Total Deaths','Total Recovered','Comfirmed Variation','Deaths Variation','Comfirmed Rate','Deaths Rate']
NaN_0_headers = ['Total Comfirmed','Total Deaths','Total Recovered','Comfirmed Variation','Deaths Variation','Comfirmed Rate','Deaths Rate']
int_headers = ['Total Comfirmed','Total Deaths','Total Recovered','Comfirmed Variation','Deaths Variation']
float_headers = ['Comfirmed Rate','Deaths Rate']

dir = os.getcwd() + '/2019-nCoV/daily_case_updates/'


def create_logger():
    handler = logging.FileHandler('DEBUG.log', mode='a')
    handler.setLevel(logging.NOTSET)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
logger = create_logger()


# git pull https://github.com/CSSEGISandData/2019-nCoV.git by crontab every hour
def csvToJson(date):
    date = datetime.strptime(date, "%Y-%m-%d").date()
    logger.info("Get data of input date")
    filename = dateToFile(date)
    if not filename:
        logger.error("No data of input date")
        return None    
    data = process(filename)
    logger.info("Get data of last date")
    last_date = date - timedelta(days=1)
    last_filename = dateToFile(last_date)
    if not last_filename:
        logger.info("No data of last date")
        data['Comfirmed Variation'] = data['Total Comfirmed']
        data['Deaths Variation'] = data['Total Deaths']
    else:
        last_data = process(last_filename)
        data['Comfirmed Variation'] = data['Total Comfirmed'].subtract(last_data['Total Comfirmed'], fill_value=0).astype(int)
        data['Deaths Variation'] = data['Total Deaths'].subtract(last_data['Total Deaths'], fill_value=0).astype(int)
        data['Comfirmed Variation'] = data['Comfirmed Variation'].apply(lambda x: 0 if x < 0 else x)
        data['Deaths Variation'] = data['Deaths Variation'].apply(lambda x: 0 if x < 0 else x)
    data['Comfirmed Rate'] = (data['Comfirmed Variation']/data['Total Comfirmed']).astype(float)
    data['Deaths Rate'] = (data['Deaths Variation']/data['Total Deaths']).astype(float)
    data['Deaths Rate'].fillna(0, inplace=True)
    for header in NaN_0_headers:
        data[header].fillna(0, inplace=True)
        if header in int_headers:
            data[header] = data[header].astype(int)
        if header in float_headers:
            data[header] = data[header].astype(float)
    data = data.reset_index()
    data['Province/State'] = data['Province/State'].replace(to_replace={'nan':''})
    data_json = data.to_json(orient='records',indent=4)
    return data_json    
    

def dateToFile(date):
    try:        
        date_new = date.strftime("%m-%d-%Y")
        regex = "^%s_(\d+)\.csv$" % (date_new)
        logger.debug("Regex: " + regex)
        filedict = dict()
        for file_candidate in os.listdir(dir):
            find = re.search(regex, file_candidate)
            if find:
                filedict[find.group(0)] = find.group(1)
        logger.debug("Candidate File: " + str(filedict))
        filename = max(filedict.items(), key=operator.itemgetter(1))[0]
        logger.debug("Newest File: " + filename)
        return filename
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error("No match Filename")
        return False
    

def process(filename):
    file = dir + filename
    logger.debug("File: " + file)
    data = pd.read_csv(file)
    data = data.rename(columns=headers)
    data = data[data.columns.intersection(allow_headers)]
    for header in allow_headers:
        if header not in data:
            data[header] = 0
    data['Country/Region'] = data['Country/Region'].replace(to_replace=China)
    for key,value in us_state_abbrev.items():
        data['Province/State'] = data['Province/State'].apply(lambda x: value if key in str(x) else str(x))
    for key,value in canada_state_abbrev.items():
        data['Province/State'] = data['Province/State'].apply(lambda x: value if key in str(x) else str(x))
    data.set_index(keys = ['Province/State','Country/Region'], inplace=True)
    data = data.groupby(['Province/State','Country/Region']).sum()
    return data


# EXPIRED
# download https://docs.google.com/spreadsheets/d/1wQVypefm946ch4XDp37uZ-wartW4V7ILdg-qYiDXUHM/htmlview?sle=true with download_xlsx.py by crontab every hour
def dataToJson(filename):
    filename = './2019-nCoV.xlsx'
    sheet = pd.read_excel(filename,sheet_name=None)
    list_sheet = list(sheet.items())
    list_sheet.reverse()
    dict_sheet = dict(list_sheet)
    newest = dict()
    i = 0
    for tab,data in dict_sheet.items():
        if tab == "Announcement":
            continue
        date = tab.split('_')[0]
        data = data.rename(columns=headers)        
        data = data[data.columns.intersection(allow_headers)]
        for header in allow_headers:
            if header not in data:
                data[header] = 0
        for header in NaN_0_headers:
            data[header].fillna(0, inplace=True)
            if header in int_headers:
                data[header] = data[header].astype(int)
            if header in float_headers:
                data[header] = data[header].astype(float)
        data['Country/Region'] = data['Country/Region'].replace(to_replace=China)
        for key,value in us_state_abbrev.items():
            data['Province/State'] = data['Province/State'].apply(lambda x: value if key in str(x) else str(x))
        data.set_index(keys = ['Province/State','Country/Region'], inplace=True)
        data = data.groupby(['Province/State','Country/Region']).sum()
        if i == 0:
            data['Comfirmed Variation'] = data['Total Comfirmed']
            data['Deaths Variation'] = data['Total Deaths']
        else:
            newest[date] = data
            now_index = list(newest.keys()).index(date)
            last_key = list(newest.keys())[now_index-1]
            last_data = list(newest.values())[now_index-1]        
            data['Comfirmed Variation'] = data['Total Comfirmed'].subtract(last_data['Total Comfirmed'], fill_value=0).astype(int)
            data['Deaths Variation'] = data['Total Deaths'].subtract(last_data['Total Deaths'], fill_value=0).astype(int)
            data['Comfirmed Variation'] = data['Comfirmed Variation'].apply(lambda x: 0 if x < 0 else x)
            data['Deaths Variation'] = data['Deaths Variation'].apply(lambda x: 0 if x < 0 else x)
        data['Comfirmed Rate'] = (data['Comfirmed Variation']/data['Total Comfirmed']).astype(float)
        data['Deaths Rate'] = (data['Deaths Variation']/data['Total Deaths']).astype(float)
        data['Deaths Rate'].fillna(0, inplace=True)
        newest[date] = data
        i += 1
        
    total = dict()
    year = datetime.now().year
    for key,value in newest.items():
        value = value.reset_index()
        value['Province/State'] = value['Province/State'].replace(to_replace={'nan':''})
        date_key = datetime.strptime(str(year) + key, "%Y%b%d").date()
        total[str(date_key)] = [y.iloc[0,:].to_dict() for x , y in value.groupby(level=0)]
    
    return total
