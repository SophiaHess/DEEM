# Data Enrichment Basic Firm-level

This folder contains a set of scripts for basic data enrichment on the firm level, including Website Status Check, Imprint Information, Geolocation, and NUTS-ID extraction. These steps are executed in sequence to enhance the dataset with valuable location and status information for each firm.

**Enrichment Steps**

1. **Website Status Check**
   - head request to check if a website is available
2. **Imprint Crawling with Netestate**
   - api request for available websites
3. **Geolocation Extraction with Geopy**
   - get latitude and longitude for your startup addresses from the imprint crawling
4. **Nuts Code Extraction**
   - searches for nuts code based on startup postal codes

To execute the script, make sure the recommended environment is activated, or you have installed all dependencies.
When starting the script, you need to pass the path to the config file, that contains all necessary information such as api keys.
An example config file can be found in `.config`. To execute the script, use the following command:
````
.\data_enrichment_from_imprint_crawling.py -f ..\.config\example.ini
````

**Script for Scraping Website Descriptions**

Additionally, a data processing script enhances the enrichment data by scraping startup website descriptions and preparing them for further analysis. This script reads a configuration file and a CSV containing URLs.

The output includes cleaned, translated descriptions saved in a CSV.

## Preparation Steps
Before you are able to execute the code you need to prepare the following:
1. **Connect to your database**
   - in the example script we use csv files
   - one potential database to use is 'Airtable': (find more information about [Airtable](https://www.airtable.com/)) ($PAID OPTION)
   - you can use whatever database is suitable for your project
3. **Get api key for Netestate or other imprint crawling services**
   - [Netestate](https://www.netestate.de/) ($PAID OPTION)
   - you can use any imprint crawling service
4. **Get your personal client for open street maps and specify it in config**
   - to access open street maps you need a client
   - create yourself a client and specify it in the `.config` file
5. **Download postal code - NUTS3 code csv from Eurostat**
   - [Download link Eurostat](https://gisco-services.ec.europa.eu/tercet/flat-files)
   - More information about NUTS encoding and APIs are accessible [here](https://gisco-services.ec.europa.eu/distribution/v2/nuts/download/)

## Columns database required
Minimum requirement `startup_website`.


## Expected Results
The script downloads the required data directly from your database and uploads the fields that are created and enriched with data during the process. 

After running both scripts successfully, you should have enriched your dataset in the following columns:
 `startup_website_status`, `startup_postal`, `startup_city`, `startup_street`, `startup_longitude`, `startup_latitude`, `startup_nuts3_code`,  `startup_website_description`


 ## Ethical & legal considerations:
When scraping data from websites, researchers must adhere to the following ethical and legal standards:
- Respect the 'robots.txt' file: The 'robots.txt' file specifies areas of the website that should or should not be accessed by automated tools. Researchers must ensure their scraping activities comply with these directives to align with the site owner’s preferences.
- Collect only publicly accessible information: Data such as general descriptions, text content, or imprints (e.g., address information) can be collected as they are typically not subject to copyright.
- Avoid scraping restricted or sensitive content, such as email addresses or other personal information.
- Compliance with copyright and privacy laws: Ensure that scraping activities do not violate intellectual property or data protection laws.

