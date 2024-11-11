# Data Enrichment LinkedIn Founder-level

The enrichment of founders consists of two scripts that perform the following functions
1. **Linkedin Profile Scraping**
   - get publicly available information about people in the dataset e.g work experience, education, profile about, skills
2. **Profile Data Processing**
   - process the raw linkedin data into structured data
   - e.g. total work experience time, highest level of education

To execute the scripts, make sure the recommended environment is activated, or you have installed all dependencies.


## Scraping
The startup scraping process is run with the script **founders_linkedin_scrape.py**

The scraping script uses linkedin urls from csv and uploads data into csv as it scrapes. 
Run the script by passing your config file after the `-f` flag 
````
python ./founders_linkedin_scrape.py -f ../../.config/example.ini
````

The script iterates through each person, visits their profile and their sub-pages and scrapes their data.
After visiting each sub-page (experience, education, skills, awards etc.), the scraped data is extracted into a csv file.


## Processing Scraped Data
The **founders_processing_notebook_ipynb** script, processes the raw scraped data that was scraped in the previous step.

The config file is also required, for this script:
````
python ./founders_linkedin_scrape.py -f ../../.config/example.ini
````

This script iterates through each persons' scraped data and processes into the structured data columns.
