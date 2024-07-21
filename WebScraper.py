from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import json

class WebScraper:

    def __init__(self):
        # Create an instance of ChromeDriverManager(CDM) to install CDM if it is not detected
        chrome = ChromeDriverManager()
        service = Service(chrome.install())
        #Server doesn't have a display so we don't need to see an open instance of chrome
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        #Class attributes
        self.scraped = False
        self.root = "https://www.governmentjobs.com"
        self.driver = webdriver.Chrome(service=service, options=options)
        self.pgNum = 1

    def scrape(self) -> None:
        jobs =[]

        while True:
            url = self.root + f"/careers/lacity?page={self.pgNum}"
            self.driver.get(url)
                
            #Ensures html isn't parsed until the tags we need are rendered
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'item-details-link')),
                    EC.presence_of_element_located((By.CLASS_NAME, 'not-found-text'))
                )
            )
            html = BeautifulSoup(self.driver.page_source, "lxml")

            if html.find('h2', class_ = 'not-found-text'): break

            for job in html.find_all('li', class_ = 'list-item'):
                link = self.root + job.find('a', class_ = 'item-details-link').get('href')
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

            self.pgNum += 1
        self.driver.quit()
        self.scraped = True
        with open('C:\wamp64\www\MyVersGPT\jobs.json', 'w') as file:
             json.dump(jobs, file, indent=4)

    def hasScraped(self) -> bool:
         return self.scraped

    def lastIndex(self, cat) -> int:
            for i in range(len(cat) - 1, 0, -1):
                if cat[i] != ' ': return i

    def getSalary(self, job) -> str:
        tags = [tag for tag in job.find_all('li') if 'class' not in tag.attrs]
        salHtml = tags[1].text
        i = salHtml.find('$')
        return salHtml[i:salHtml.find('n') - 2]