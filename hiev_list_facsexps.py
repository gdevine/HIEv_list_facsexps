'''
Python script to perform a scrape of the HIEv users list and create a readable csv file of the information which
is then uploaded into hiev

Author: Gerard Devine
Date: August 2015


- Note: This script can only be performed by a HIEv admin  

'''

import os
import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup
import html2text
import unicodecsv as csv
from datetime import datetime
import requests

# Browser
br = mechanize.Browser()
# Cookie Jar
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)
# Browser options
br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
br.addheaders = [('User-agent', 'Chrome')]



# Navigate to and open the hiev login page 
br.open('https://hiev.uws.edu.au/users/sign_in')

# Select the actual login form in the html
br.select_form(nr=0)

# Fill in user email and password via preset environment variables 
br.form['user[email]'] = os.environ['AdminEmail']
br.form['user[password]'] = os.environ['AdminPass']

# login to the site
br.submit()
html_text = br.open('https://hiev.uws.edu.au/users').read()
soup = BeautifulSoup(html_text)

# scrape the user information and write it out to datestamped csv file 
csvfilename = 'HIEv_User_List_'+datetime.now().strftime('%Y%m%d')+'.csv'
with open(csvfilename, 'wb') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', encoding='utf-8')
    # Write header line
    csvwriter.writerow(["User ID", "Email", "First Name", "Surname"])
    all_entries = soup.findAll('tr', {'class': 'field_bg'}) + soup.findAll('tr', {'class': 'field_nobg'})
    for entry in all_entries:
        id = entry.find('a')['href'].split('/')[-1]
        email = entry.find('td', {'class':'email'}, 'a').text.encode('utf-8')
        
        names = entry.findAll('td', {'class':'name'})
        firstname =  names[0].text.encode('utf-8')
        surname =  names[1].text.encode('utf-8')
        
        csvwriter.writerow([id, email, firstname, surname])
        
csvfile.close()


#
# Now upload the file into HIEv
#

# Set global variables for upload
api_token = os.environ['HIEV_API_KEY']
upload_url = 'https://hiev.uws.edu.au/data_files/api_create.json?auth_token='+api_token
filename = csvfilename
dest_dir = os.path.dirname(__file__)

# set metadata fields before upload
filetype = "PROCESSED"
experiment_id = 77
start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
description = "A list of current HIEv users in CSV format, including the ID, email, first name, and surname"
format = "CSV"

# Upload the file (with metadata) to HIEv   - defalt is private access is applied
upload_file = {'file': open(os.path.join(dest_dir, csvfilename), 'rb')}
payload = {'type':filetype, 'experiment_id': experiment_id, 'start_time': start_time, 'end_time': end_time, 'description': description, 'format':format }
r = requests.post(upload_url, files=upload_file, data=payload)
