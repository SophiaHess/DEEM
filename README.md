# Dynamic entrepreneurial ecosystem monitoring (DEEM)

This repository contains scripts to create a dataset for entrepreneurial ecosystem research as explained in the work [Dynamic entrepreneurial ecosystem monitoring: 
A toolkit for dataset creation] by Sophia Hess.

The provided scripts cover the following: 
- **Basic Enrichment:** website activity check, headquarter address, geolocation, nuts encoding
- **LinkedIn Enrichment Firm-level:** LinkedIn url, website, about us, company size, founding year, no. of employees, main university employees, industry
- **LinkedIn Enrichment Founder-level:** LinkedIn url, work experience, skills, highest level of education, PhD

Minimum requirement: firm name *AND* website *AND/OR* LinkedIn profile.

## Motivation
By sharing this repository, we aim to provide a toolset on how to build and maintain a traceable and updated dataset for entrepreneurial ecosystem research, using puplicly available data. We combine different data sources to detect startups at a very early stage, follow the startup cohort over time, and to create a comprehensive dataset that allows us to apply AI models in the future. We encourage fellow scholars to create similar datasets in other contexts, allowing for panel studies, applying comparable entrepreneurial ecosystem measures and advancing the research program by providing more data-centric approaches to study the entrepreneurial ecosystem phenomenon.

## Dependencies
All scripts are written in Python and we have provided all required libraries to run our scripts in the environment.yml file. You can recreate our virtual environment to run the scripts on your computer using Anaconda ([Installation guide](https://docs.anaconda.com/anaconda/install/index.html)). To regenerate the virtual environment use the following command:
````
conda env create -f environment.yml
````
After recreating be sure to activate the environment. 
````
conda activate deem
````

## Create your own dataset
To execute any of the scripts, you need to go to the specific folder and specify all your parameters (e.g., API keys) in the `.config` file. Example.in provides the expected config file structure (e.g., required API keys). To run each script you can modify the following command:
````
python SCRIPTNAME.py -f PATHTOCONFIG.ini
````
Further detailed explanations can be found in the `README.md`.
