# Dynamic Entrepreneurial Ecosystem Monitoring (DEEM)

This repository contains scripts to create a dataset for entrepreneurial ecosystem (EE) research as explained in the work [*Empirical Entrepreneurial Ecosystem Research: A Guide to Creating Multilevel Datasets*] by Sophia Hess.

The guide to creating multilevel EE datasets includes four consecutive steps: data collection, enrichment, validation, and monitoring. 

The provided scripts mainly cover the process steps for data enrichment:
- **Basic Enrichment:** website activity check, headquarter address, geolocation, nuts encoding
- **LinkedIn Enrichment Firm-level:** LinkedIn url, website, about us, company size, founding year, no. of employees, industry
- **LinkedIn Enrichment Founder-level:** LinkedIn url, education background, work experience, skills

Initial guidance for validation procedures are also provided. 

**Minimum requirement:** firm website *AND/OR* LinkedIn profile.

## Motivation
By sharing this repository, we aim to provide a guide on how to build and maintain a traceable and updated datasets for multilevel EE research, using puplicly available data. We combine different data sources to detect startups at a very early stage, follow the startup cohort over time, and create a comprehensive dataset that allows us for longitudinal studies and applying AI models in the future. We encourage fellow scholars to create similar datasets in other contexts to empirically study the EE phenomenon and to provide data for evidence-based policy design, implementation, and evaluation.

## Dependencies
All scripts are written in Python and we have provided all required libraries to run our scripts in the environment.yml file. You can recreate our virtual environment to run the scripts on your computer using Anaconda ([Installation guide](https://docs.anaconda.com/anaconda/install/index.html)). To regenerate the virtual environment use the following command:
````
conda env create -f environment.yml
````
After recreating be sure to activate the environment. 
````
conda activate deem
````
Make sure you install the database dependencies needed for your project. In our example case using Airtable, we install:
````
pip install pyairtable==1.2.0
````

## Create your own dataset
To execute any of the scripts, you need to go to the specific folder and specify all your parameters (e.g., API keys) in the `.config` file. Example.in provides the expected config file structure (e.g., required API keys). To run each script you can modify the following command:
````
python SCRIPTNAME.py -f PATHTOCONFIG.ini
````
Further detailed explanations can be found in the `README.md` of each folder.
