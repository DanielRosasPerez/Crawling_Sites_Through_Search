import requests
from bs4 import BeautifulSoup
from time import sleep
import random, csv
# SELENIUM (JUST IN CASE THE PAGES ARE DYNAMICALLY LOADED):
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def setting_driver(url):
    """This functions sets a driver."""

    driver = None  # To avoid have multiple driver instances opened at the same time.

    opts = Options()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome("./chromedriver.exe", options=opts)
    driver.get(url)
    return driver


def save_data(file_name, content_list):
    """This function saves the retrieved data."""

    assert file_name.split('.')[-1] == "csv", "THE FILE EXTENSION MUST BE 'csv'."

    with open(f"{file_name}", "a") as csv_outfile:
        field_names = ("Topic", "Title", "Description", "URL")
        csv_writer = csv.DictWriter(csv_outfile, fieldnames=field_names, lineterminator='\n')
        csv_writer.writeheader()
        for data in content_list:
            try:
                csv_writer.writerow({"Topic":data.topic, "Title":data.title, "Description":data.body, "URL":data.url})
            except Exception as e:
                print("There was something wrong when saving the data. Let's try with the next one.")
                print(f"By the way, the error is the following: \n{e}")

class Content:
    """Common base class for all articles/pages"""

    def __init__(self, topic, title, body, url):
        self.topic = topic
        self.title = title
        self.body = body
        self.url = url

    def print(self):
        """
        Flexible printing function controls output
        """
        print('New article found for topic: {}'.format(self.topic))
        print('URL:\n{}'.format(self.url))
        print('TITLE:\n{}'.format(self.title))
        print('BODY:\n{}'.format(self.body))


class Website:
    """Contains information about website structure"""

    def __init__(self, name, url, searchUrl, resultListing, resultUrl, absoluteUrl, titleTag, bodyTag):
        self.name = name
        self.url = url
        self.searchUrl = searchUrl
        self.resultListing = resultListing
        self.resultUrl = resultUrl
        self.absoluteUrl = absoluteUrl
        self.titleTag = titleTag
        self.bodyTag = bodyTag


class Crawler:

    def getPage(self, url):
        try:
            req = requests.get(url)
        except requests.exceptions.RequestException:
            return None
        return BeautifulSoup(req.text, 'html.parser')

    def safeGet(self, pageObj, selector):
        childObj = pageObj.select(selector)
        if childObj is not None and len(childObj) > 0:
            return '\n'.join([child.text.replace('\n','').replace('\r','').replace('\t','').strip()
                              for child in childObj])
        return ''

    def search(self, topic, site):
        """
        Searches a given website for a given topic and records all pages found
        """
        bs = self.getPage(site.searchUrl + topic)
        searchResults = bs.select(site.resultListing)
        if not searchResults:  # Just in case the website is dynamic. It means, we're not able to retrieve data using
            # using the method "getPage", since the data we're looking for isn't in the main html tree.
            driver = setting_driver(site.searchUrl + topic)
            sleep(random.uniform(3.0,3.5))
            bs_object = BeautifulSoup(driver.page_source, "lxml")
            searchResults = bs_object.select(site.resultListing)
        for result in searchResults:
            try:
                url = result.select(site.resultUrl)[0].attrs['href']
            except Exception as e:
                print('Something was wrong with that page or URL. Let\'s try with the next one.')
                print(f"By the way, the error is the following: \n{e}")
                print('#' * 60)
                continue
            # Check to see whether it's a relative or an absolute URL
            if(site.absoluteUrl):
                bs = self.getPage(url)
            else:
                bs = self.getPage(site.url + url)
            if bs is None:
                print('Something was wrong with that page or URL. Skipping!')
                return None  # We exist from this method if something went wrong and we return None.
            title = self.safeGet(bs, site.titleTag)
            body = self.safeGet(bs, site.bodyTag)
            if title != '' and body != '':
                content = Content(topic, title, body, url)
                content_list.append(content)
                content.print()
                print('#' * 60)
        try:
            driver.close()  # In case we've used a driver we close the session;
        except:
            pass  # Otherwise, we just pass and continue with the next website.

#####################################################################################################

crawler = Crawler()

siteData = [
    ['O\'Reilly Media', 'http://oreilly.com', 'https://www.oreilly.com/search/?query=',
    'article[data-testid=searchCard]', 'h4[class*="Title"] > a', False, 'h1',
    'div.content > span p, div.content > span ul'],
    ['Reuters', 'http://reuters.com', 'http://www.reuters.com/search/news?blob=',
    'div.search-result-content', 'h3.search-result-title a', False, 'h1',
    'div.StandardArticleBody_body_1gnLA'],
    ['Brookings', 'http://www.brookings.edu',
    'https://www.brookings.edu/search/?s=', 'div.list-content article',
    'h4.title a', True, 'a + h1.report-title', 'div.post-body']
]
sites = []
for row in siteData:
    sites.append(Website(row[0], row[1], row[2],
                         row[3], row[4], row[5], row[6], row[7]))

topics = ['python', 'data science']
content_list = list()
for topic in topics:
    print('GETTING INFO ABOUT: ' + topic)
    for targetSite in sites:
        crawler.search(topic, targetSite)

# Saving data:
save_data("articles_data.csv", content_list)
