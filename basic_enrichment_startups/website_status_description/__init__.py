import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def extract_description(url):
    try:
        response = requests.get(url, timeout=20, allow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')

        metas = soup.find_all('meta')

        for meta in metas:
            if 'name' in meta.attrs and meta.attrs['name'] == 'description':
                if 'content' in meta.attrs.keys():
                    description = meta.attrs['content'] + ' - automatically generated'
                    description.encode()  # ensure string is encoded in utf-8
                    return description
                else:
                    print('error with ', url)

    except requests.ConnectionError or IndexError:
        print(url, ' ------- ', "failed to connect")
    except requests.Timeout:  # could also be specified to ConnectTimeout or ReadTimeout
        print(url, ' ------- ', "connection timeout")
    return


def url_formatting(url):
    if url.startswith('https://'):
        return 'https://' + url
    else:
        return url


def check_url_status(url):
    """sends request to website in record and returns tuple with website status and alternative website"""
    valid_responses = [200, 402, 403, 405, 406]
    try:
        # configure request to follow redirect and timeout after 15 seconds
        request = requests.head(url, timeout=15, allow_redirects=True)

        # check for redirects
        if not request.history:  # no redirect
            # add status code and reason to data list with record id
            if request.status_code in valid_responses:
                return 'website available', ''
            else:
                return f'{request.status_code} - {request.reason}', ''
        else:  # redirect
            # add status code and reason for original url to data list with record id and also ad the url it's
            # directed to
            return f'{request.history[0].status_code} - {request.history[0].reason}', request.url

    except requests.exceptions.MissingSchema:
        # url_2 = url_formatting(url)
        #####################################
        return "MissingSchema", ''
    except requests.ConnectionError:
        return "failed to connect", ''
    except requests.Timeout:  # could also be specified to ConnectTimeout or ReadTimeout
        return "connection timeout", ''
    except requests.exceptions.TooManyRedirects:
        return "redirect error", ''
    except (requests.exceptions.InvalidSchema, requests.exceptions.InvalidURL) \
            as error:
        return "invalid url", ''
    except KeyError:  # when record["fields"]["startup_website"] fails because of missing url in airtable
        return "missing url", ''


def get_status_for_urls(startup_data):
    """send requests for each website in startup dataframe and get response codes in new column"""
    # create new pandas methods that use tqdm progress tracker
    tqdm.pandas()

    # send requests for websites
    print('sending requests for websites:')
    startup_data['startup_website_status'], startup_data['startup_alternative_website'] = \
        zip(*startup_data['startup_website'].progress_apply(check_url_status))

    # retry 4 more times for startups with failed to connect values
    print('retrying websites with failed to connect status')
    if startup_data['startup_website_status'].str.contains('failed to connect').any():
        # ran into 'not enough values to unpack' error. Guessing that happens when there are no failed to connect entries -> if clause should avoid that
        for i in range(4):
            print(f'try number {i + 2} for failed to connect')
            startup_data.loc[(startup_data['startup_website_status'] == 'failed to connect'), 'startup_website_status'], \
            startup_data.loc[
                (startup_data['startup_website_status'] == 'failed to connect'), 'startup_alternative_website'] = \
                zip(*startup_data.loc[
                    (startup_data['startup_website_status'] == 'failed to connect'), 'startup_website'].progress_apply(
                    check_url_status))
    else:
        print('check: all given websites reached in first go')

    return startup_data
