# Data Enrichment LinkedIn Startups

This enrichment procedure contains two steps and therefore also two seperate scripts:
1. **LinkedIn URL Search**
   - for Startups in your dataset that have no LinkedIn URL
2. **LinkedIn Scraping**
   - get publicly available information about firms in your dataset
   - e.g., founding year, number of employees, company size, website, industry type, etc. 

To execute the script, make sure the recommended environment is activated, or you have installed all dependencies.
When starting the script, you need to pass the path to the config file, that contains all necessary information such as LinkedIn login credentials
An example config file can be found in `.config`.

## Preparation Steps
As a basic requirement you need to activate a LinkedIn account (premium account recommended). Specify your login credentials in the `.config` file.

The startup scraping process consists of two scripts:
1. **startup_linkedin_search.py**
2. **startup_linkedin_scraper.py**

The following steps should be taken to enhance the startup information in your database:

1. Create a config file containing all the necessary information for both scripts. An example that contains all the necessary fields can be found in `.config/example.ini`
2. Run the script by passing your config file after the `-f` flag 
````
python .\startup_linkedin_search.py -f .\.config\example.ini
````
3. **CAUTION**: For all LinkedIn URLs you have drawn directly via the LinkedIn search you need to hand check the `.csv` file created in the output folder. 
   - check the records that failed the website comparison (LinkedIn website vs. website from your database)
   - if you have no website for your record, check whether the profile is correct 
   - if you can confirm a failed LinkedIn URL as correct - mark cell with 'Corrected'
   - read manually checked csv file from path specified in `.config` file
   
4. Run startup_linkedin_scraper.py with the valid LinkedIn URLs by passing your config file after `-f`
````
python .\startup_linkedin_scraper.py -f .\.config\example.ini 
````

## Columns database required
1. **LinkedIn URL Search**: 
   - `startup_name` (mandatory)
   - `startup_website` (optional, to do url comparison)
2. **LinkedIn Scraping**:
   - `startup_linkedin_url`

## Expected Results
The script will extract the following information for startups if available:
- `main_university_employees_linkedin`: indicates which university most employees have studied
- `n_linkedin_employees`: number of employees with LinkedIn profile
- `founding_year_linkedin`: founding year specified by page owner
- `company_size_linkedin`: rough range of employee number (self select option)
- `industry_linkedin`: self selected industry classification
- `about_us_linkedin`: startup description from about page
- `employee_list_linkedin`: list of json elements for each employee (name, designation, profile url)



#### *References*
*LinkedIn scraper is based on previous work from: [joeyism/linkedin_scraper](https://github.com/joeyism/linkedin_scraper)*
