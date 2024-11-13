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
.\founders_linkedin_scrape.py -f ..\..\.config\example.ini
````

The script iterates through each person, visits their profile and their sub-pages and scrapes their data.
After visiting each sub-page (experience, education, skills, awards etc.), the scraped data is extracted into a csv file.


## Processing scraped data
The **founders_processing_notebook_ipynb** script, processes the raw scraped data that was scraped in the previous step.

This script iterates through each persons' scraped data and processes into the structured data columns.

## Expected results
The script will extract the following information for founders if available:
- `affiliated_university_founder`: indicates which university the founder got the highest degree from
- `highest_education_level`: Bachelor, Master, PhD, MBA, etc.
- `study_time`: how long did the founder study
- `work_experience`: duration of work experience, last job before founding a startup
- `founding_experience`: first-time or serial
- `current_company`: current employment in work experience
- `job_title`: current job title
- `field_of_study`: study field from highest degree
- `certificates`: e.g., leadership certificates, project management certificates, scrum master, etc.
- `social_engagement_in_voluntary work`: e.g., leadership certificates, project management certificates, scrum master, etc.


## Ethical & legal considerations:
When scraping data from LinkedIn, researchers must adhere to strict ethical and legal guidelines to ensure compliance with LinkedIn’s terms of service:
- Limit Data to Publicly Available Information: Avoid scraping sensitive or private data. Ensure data is not used for commercial or third-party purposes.
- Avoid Excessive Automation: Excessive or unauthorized scraping can lead to account restrictions, suspension, or legal consequences.
- Data Anonymization and Security: Store all collected data securely and in anonymized form to protect user privacy.
- Request Permission: Use Data Access for Researchers if you want to compose large-scale datasets that exceed manual profile validation.

Evolving LinkedIn policy:
- LinkedIn policies and available tools (e.g., API services) have changed over time. As of August 2023, Data Access for Researchers is the primary channel for accessing LinkedIn at large scale.
