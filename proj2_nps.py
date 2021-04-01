#################################
##### Name: Guan-Ying Lai
##### Uniqname: evylai
#################################

from bs4 import BeautifulSoup
import requests
import json
import secret # file that contains your API key



class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def  __init__(self, category, name, address, zipcode, phone):
            self.category = category
            self.name = name
            self.address = address
            self.zipcode = zipcode
            self.phone = phone

        
    
    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"

CACHE_FILENAME = "nps_cache.json"
CACHE_DICT = {}

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def make_request_with_cache(site_url, cache):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    baseurl: string
        The URL for the sites

    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    if site_url in cache.keys():
        print("Using Cache")
        return cache[site_url]
    else:
        print("Fetching")
        response = requests.get(site_url)
        cache[site_url] = response.text
        save_cache(cache)
        return cache[site_url]

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    baseurl = "https://www.nps.gov"
    response = make_request_with_cache(baseurl, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    search_bar = soup.find('body').find_all('div', class_='SearchBar')
    menu = search_bar[0].find('ul', class_="dropdown-menu")
    links = menu.find_all('a')
    state_urls = {}
    for link in links:
        state_urls[link.text.lower()] = baseurl + link.get('href')
    return state_urls
       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = make_request_with_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    parks_hero = soup.find(id="HeroBanner").find_all(class_='col-sm-12')
    parks_footer = soup.find(id="ParkFooter").find_all(class_='ParkFooter-contact')
    try:
        park_name = parks_hero[0].find('a').text
    except:
        park_name = "no name"
    try:
        park_category = parks_hero[0].find(class_='Hero-designation').text.replace("\n", "")
    except:
        park_category = "no category"
    try:
        park_city = parks_footer[0].find(itemprop="addressLocality").text.replace("\n", "")
    except:
        park_city = "no city"
    try:
        park_state = parks_footer[0].find(itemprop="addressRegion").text.replace("\n", "")
    except:
        park_state = "no state"
    try:
        park_zipcode = parks_footer[0].find(itemprop="postalCode").text.replace(" ", "")
    except:
        park_zipcode = "no zip code"
    try:
        park_phone = parks_footer[0].find(itemprop="telephone").text.replace("\n", "")
    except:
        park_phone = "no phone"

    park_address = f"{park_city}, {park_state}"

    return NationalSite(park_category, park_name, park_address, park_zipcode, park_phone)
    



def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    baseurl = "https://www.nps.gov"
    response = make_request_with_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    parks = soup.find(id="list_parks").find_all(class_="clearfix")
    parks_list = []
    for park in parks:
        park_url = park.find("h3").find_all('a')[0]
        link = baseurl + park_url.get("href")
        parks_list.append(link)
    parks_instance_list = []
    for park_list in parks_list:
        parks_instance_list.append(get_site_instance(park_list))

    return parks_instance_list

api_key = secret.API_KEY


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    base = "http://www.mapquestapi.com/search/v2/radius"
    params={
        'key': api_key,
        'origin': site_object.zipcode,
        'radius': 10,
        'maxMatches': 10,
        'ambiguities': "ignore",
        'outFormat': "json"
    }
    param_strings = []
    for k, v in params.items():
        param_strings.append(f"{k}_{v}")
    param_strings.sort()
    request_key = f"{base}_{param_strings}"
    if request_key in CACHE_DICT.keys():
        print("Using Cache")
        return CACHE_DICT[request_key]
    else:
        print("Fetching")
        response = requests.get(base, params=params)
        CACHE_DICT[request_key] = response.json()
        save_cache(CACHE_DICT)
        return CACHE_DICT[request_key]


if __name__ == "__main__":
    while True:
        name = input("Enter a state name (e.g. Michigan, michigan) or 'exit': ")
        name_dict = build_state_url_dict()
        if name == "exit":
            exit()
        elif name.lower() not in name_dict.keys() :
            print(f"[Error] Enter proper state name")
            pass
        else:
            state_url = build_state_url_dict()[name.lower()]
            CACHE_DICT = open_cache()
            parks = get_sites_for_state(state_url)
            print("--------------------------------------")
            print(f"List of national sites in {name}")
            print("--------------------------------------")
            for i in range(len(parks)):
                print(f"[{i+1}] {parks[i].info()}")
                i+=1
            print("--------------------------------------")
            choice = input("Choose the number for detail search or 'exit' or 'back': ")
            print("--------------------------------------")
            if choice == "back":
                pass
            elif choice == "exit":
                exit()
            elif int(choice) > len(parks):
                print(f"[Error] Invalid input")
            else:
                instance = parks[int(choice)-1]
                results = get_nearby_places(instance)["searchResults"]
                print(f"Place near {instance.name}")
                print("--------------------------------------")
                for result in results:
                    if result["fields"]["name"] == "":
                        near_name = "no name"
                    else:
                        near_name = result["fields"]["name"]
                    if result["fields"]["group_sic_code_name"] == "":
                        near_category = "no category"
                    else:
                        near_category = result["fields"]["group_sic_code_name"]
                    if result["fields"]["address"] == "":
                        near_address = "no address"
                    else:
                        near_address = result["fields"]["address"]
                    if  result["fields"]["city"] == "":
                        near_city = "no city"
                    else:
                        near_city = result["fields"]["city"]
                    print(f"- {near_name} ({near_category}): {near_address}, {near_city}")
                pass


