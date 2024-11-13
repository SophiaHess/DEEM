# Data Enrichment LinkedIn Firm-level

This enrichment procedure contains two steps and therefore also two seperate scripts:
1. **LinkedIn URL Search**
   - for Startups in your dataset that have no LinkedIn URL you use the **startup_linkedin_search.py**
2. **LinkedIn Scraping**
   - get publicly available information about firms in your dataset via **startup_linkedin_scraper.py**
   - e.g., founding year, number of employees, company size, website, industry type, etc. 

To execute the script, make sure the recommended environment is activated, or you have installed all dependencies.
When starting the script, you need to pass the path to the config file, that contains all necessary information such as LinkedIn login credentials
An example config file can be found in `.config`.

## Run startup_linkedin_search.py 
- Run the script by passing your config file after the `-f` flag
````
.\startup_linkedin_search.py -f ..\..\.config\example.ini
````

**CAUTION**: 
For all LinkedIn URLs you have drawn directly via the LinkedIn search you need to hand check the `.csv` file created in the output folder. 
   - check the records that failed the website comparison (LinkedIn website vs. website from your database)
   - if you have no website for your record, check whether the profile is correct 
   - if you can confirm a failed LinkedIn URL as correct - mark cell with 'Corrected'
   - read manually checked csv file from path specified in `.config` file
   
## Run startup_linkedin_scraper.py with the valid LinkedIn URLs
Pass your config file after `-f`
````
.\startup_linkedin_scraper.py -f ..\..\.config\example.ini
````

## Minimum information required
1. **LinkedIn URL Search**: 
   - `startup_name` (mandatory)
   - `startup_website` (optional, to do url comparison)
2. **LinkedIn Scraping**:
   - `startup_linkedin_url`

## Expected results
The script will extract the following information for startups if available:
- `main_university_employees_linkedin`: indicates which university most employees have studied
- `n_linkedin_employees`: number of employees with LinkedIn profile
- `founding_year_linkedin`: founding year specified by page owner
- `company_size_linkedin`: rough range of employee number (self select option)
- `industry_linkedin`: self selected industry classification
- `about_us_linkedin`: startup description from about page
- `employee_list_linkedin`: list of json elements for each employee (name, designation, profile url)

## Ethical & legal considerations:
When scraping data from LinkedIn, researchers must adhere to strict ethical and legal guidelines to ensure compliance with LinkedIn’s terms of service:
- Limit Data to Publicly Available Information: Avoid scraping sensitive or private data. Ensure data is not used for commercial or third-party purposes.
- Avoid Excessive Automation: Excessive or unauthorized scraping can lead to account restrictions, suspension, or legal consequences.
- Data Anonymization and Security: Store all collected data securely and in anonymized form to protect user privacy.
- Request Permission: Use Data Access for Researchers if you want to compose large-scale datasets that exceed manual profile validation.

Evolving LinkedIn policy:
- LinkedIn policies and available tools (e.g., API services) have changed over time. As of August 2023, Data Access for Researchers is the primary channel for accessing LinkedIn at large scale.

#### *References*
*LinkedIn scraper is based on previous work from: [joeyism/linkedin_scraper](https://github.com/joeyism/linkedin_scraper)*
