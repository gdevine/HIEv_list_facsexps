'''
Python script to perform a scrape of the HIEv facilities and experiments list and create a csv file of each before then 
uploading them into hiev

Author: Gerard Devine
Date: September 2015


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


#set the base URL of HIEv
base_url = "https://hiev.uws.edu.au"

# Navigate to and open the hiev login page 
br.open(base_url+'/users/sign_in')

# Select the actual login form in the html
br.select_form(nr=0)

# Fill in user email and password via preset environment variables 
br.form['user[email]'] = os.environ['AdminEmail']
br.form['user[password]'] = os.environ['AdminPass']

# login to the site
br.submit()
html_text = br.open('https://hiev.uws.edu.au/org_level1').read()
soup = BeautifulSoup(html_text)


# scrape the information and write it out to datestamped facilty and experiment csv files

# set the filenames for each  
fac_csvfile = 'HIEv_Facilities_List_'+datetime.now().strftime('%Y%m%d')+'.csv'
exp_csvfile = 'HIEv_Experiments_List_'+datetime.now().strftime('%Y%m%d')+'.csv'
#open each file for new writing, add headers, and close again
with open(fac_csvfile, 'wb') as faccsvfile:
    faccsvwriter = csv.writer(faccsvfile, delimiter=',', encoding='utf-8')
    faccsvwriter.writerow(["Facility ID", "Name", "Code", "Description", "Top Left Corner", "Bottom Right Corner", 'Location', "Primary Contact"])
faccsvfile.close()
with open(exp_csvfile, 'wb') as expcsvfile:
    expcsvwriter = csv.writer(expcsvfile, delimiter=',', encoding='utf-8')
    expcsvwriter.writerow(["Experiment ID", "Parent Facility ID", "Name", "Description", "Start Date", "Subject"])
expcsvfile.close()
    

#Now open each file for appending the actual information, beginning with the parent facilities
with open(fac_csvfile, 'a') as faccsvfile:
    faccsvwriter = csv.writer(faccsvfile, delimiter=',', encoding='utf-8')
    
    # Loop through each individual facility in HIEv and extract info
    all_facs = soup.findAll('tr', {'class': 'field_bg'}) + soup.findAll('tr', {'class': 'field_nobg'})
    for fac in all_facs:
        #create empty array to append facility details to
        fac_record=[]
        # pull out the ID of the facility
        fac_id = fac.find('a')['href'].split('/')[-1]
        fac_record.append(fac_id)

        # Now navigate to the individual facility page to extract the rest of the information        
        facility_text = br.open(base_url + fac.find('a')['href']).read()
        soup = BeautifulSoup(facility_text)
        
        for value in ['name', 'code', 'description', 'top_left_corner', 'bottom_right_corner', 'location', 'primary_contact']:
          fac_value = soup.find(attrs={"id": value+"_display"})
          if fac_value:
            fac_record.append(fac_value['title'].replace(",", ":"))
          else:
            fac_record.append("")
              
        # Now write all the information to the facility csv file 
        faccsvwriter.writerow(fac_record)
        
        # Visit each facility experiment and extract info
#         with open(exp_csvfile, 'wb') as expcsvfile:
        with open(exp_csvfile, 'a') as expcsvfile:
            expcsvwriter = csv.writer(expcsvfile, delimiter=',', encoding='utf-8')
            
            # Loop through each individual facility in HIEv and extract info
            table = soup.find('table', id='experiments')
            all_exps = table.findAll('a', href=True)
            
            for exp in all_exps:
                #create empty array to append facility details to
                exp_record=[]
                # attach the ID of the experiment]
                exp_id = exp['href'].split('/')[-1]
                exp_record.append(exp_id)
                # attach the ID of the parent facility
                exp_record.append(fac_id)
                
                # Now navigate to the individual experiment page to extract the rest of the information        
                exp_text = br.open(base_url + exp['href']).read()
                soup = BeautifulSoup(exp_text)
                
                for value in ['name', 'description', 'start_date', 'subject']:
                  exp_value = soup.find(attrs={"id": value+"_display"})
                  if exp_value:
#                     exp_record.append(exp_value['title'].replace(",", ":"))
                    exp_record.append(exp_value['title'])
                  else:
                    exp_record.append("")
                      
                # Now write all the information to the facility csv file 
                expcsvwriter.writerow(exp_record)

         
                
faccsvfile.close()
expcsvfile.close()


#
# Now upload the file into HIEv
#
 
# Set global variables for upload
api_token = os.environ['HIEV_API_KEY']
upload_url = 'https://hiev.uws.edu.au/data_files/api_create.json?auth_token='+api_token
# filename = fac_csvfile
dest_dir = os.path.dirname(__file__)
 
# set metadata fields before upload
filetype = "PROCESSED"
experiment_id = 77
start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
fac_description = '''A list of current HIEv facilities in CSV format, including the ID, name, code, description, location details, and 
                  contact. This file can be used in conjunction with the HIEv 'experiments list' file where facilities are made up of experiments.'''
exp_description = '''A list of current HIEv experiments in CSV format, including the ID, parent facility, id, name, description, start date and 
                  subject. This file can be used in conjunction with the HIEv 'facilities list' file where facilities are made up of experiments.'''
format = "CSV"
 
# Upload both files (with metadata) to HIEv   - defalt is private access is applied
fac_upload_file = {'file': open(os.path.join(dest_dir, fac_csvfile), 'rb')}
payload = {'type':filetype, 'experiment_id': experiment_id, 'start_time': start_time, 'end_time': end_time, 'description': fac_description, 'format':format }
r = requests.post(upload_url, files=fac_upload_file, data=payload)

exp_upload_file = {'file': open(os.path.join(dest_dir, exp_csvfile), 'rb')}
payload = {'type':filetype, 'experiment_id': experiment_id, 'start_time': start_time, 'end_time': end_time, 'description': exp_description, 'format':format }
r = requests.post(upload_url, files=exp_upload_file, data=payload)
