from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time

class WebScraper:

    def __init__(self, setOptions = True):
        # Create an instance of ChromeDriverManager(CDM) to install CDM if it is not detected
        chrome = ChromeDriverManager(driver_version="127.0.6533.89")
        self.service = Service(chrome.install())

        #Server doesn't have a display so we don't need to see an open instance of chrome
        self.options = Options()
        if setOptions:
            self.options.add_argument('--no-sandbox')
            self.options.add_argument('--headless')
            self.options.add_argument('--disable-dev-shm-usage')

        #Class attributes
        self.jobScraped = False

    def scrape(self) -> None:
        jobDriver = webdriver.Chrome(service=self.service, options=self.options)
        root = "https://www.governmentjobs.com"
        pgNum = 1
        jobs =[]

        while True:
            url = root + f"/careers/lacity?page={pgNum}"
            jobDriver.get(url)
            html = BeautifulSoup(jobDriver.page_source, "lxml")
                
            #Ensures html isn't parsed until the tags we need are rendered
            WebDriverWait(jobDriver, 10).until(
                EC.any_of(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'item-details-link')),
                    EC.presence_of_element_located((By.CLASS_NAME, 'not-found-text'))
                )
            )

            if html.find('h2', class_ = 'not-found-text'): break

            for job in html.find_all('li', class_ = 'list-item'):
                link = root + job.find('a', class_ = 'item-details-link').get('href')
                jName = job.find('a', class_ = 'item-details-link').text
                cat = job.find('li', class_ = 'categories-list').text
                catText = cat[39:self.lastIndex(cat)]
                salary = self.getSalary(job)
                jobs.append({
                    'Job Title': jName,
                    'Link': link,
                    'Category': catText,
                    'Annual Salary': salary
                })

            pgNum += 1
        jobDriver.quit()
        self.jobScraped = True
        with open('C:\wamp64\www\ChatbotAPI\jobs.json', 'w') as file:
             json.dump(jobs, file, indent=4)

    def searchAssist(self, dep) -> None:
        assistDriver = webdriver.Chrome(service=self.service, options=self.options)
        url = "https://assist.org/transfer/results?year=74&institution=50&agreement=104&agreementType=from&view=agreement&viewBy=major&viewSendingAgreements=false"
        assistDriver.get(url)
        
        #Wait for the search bar to load in before attempting to type in it
        search = WebDriverWait(assistDriver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ng-valid"))
        )
        search.send_keys(dep)

        #wait for department options to load before trying to click on it
        department = WebDriverWait(assistDriver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "viewByRowColText"))
        )
        department.click()

        #wait for the sections tag to load before trying to read from it
        section = WebDriverWait(assistDriver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "template"))
        )

        time.sleep(10)

    def hasScraped(self) -> bool:
        return self.jobScraped

    def lastIndex(self, cat) -> int:
        for i in range(len(cat) - 1, 0, -1):
            if cat[i] != ' ': return i

    def getSalary(self, job) -> str:
        tags = [tag for tag in job.find_all('li') if 'class' not in tag.attrs]
        salHtml = tags[1].text
        i = salHtml.find('$')
        return salHtml[i:salHtml.find('n') - 2]