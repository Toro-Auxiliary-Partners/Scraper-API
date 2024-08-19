from selenium.common.exceptions import NoSuchElementException
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

        #Server doesn't have a display so we don't need to see an open instance of chrome unless we need it for testing purposes
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

    def searchAssist(self) -> None:
        assistDriver = webdriver.Chrome(service=self.service, options=self.options)
        url = "https://assist.org"
        assistDriver.get(url)

        #wait for the search bar to load before entering 'CSUDH' into the search bar
        WebDriverWait(assistDriver, 10).until(
            EC.presence_of_element_located((By.ID, "governing-institution-select"))
        ).send_keys('CSUDH')

        #wait for the CSUDH option to load from the dropdown menu before clicking on it
        WebDriverWait(assistDriver, 10).until(
            EC.presence_of_element_located((By.ID, 'option-202'))
        ).click()

        #wait for the search bar to load before entering a CC institution
        ccSearchBar = WebDriverWait(assistDriver, 10).until(
            EC.element_to_be_clickable((By.NAME, 'institution-agreement'))
        )

        #type the school we want tranfer class data from and then click on the 1st option from the drop down menu
        ccSearchBar.send_keys('Cerritos College')
        schoolList = WebDriverWait(assistDriver, 10).until(
            EC.presence_of_element_located((By.ID, 'cdk-overlay-1'))
        )
        school = schoolList.find_element(By.TAG_NAME, 'amc-option')
        school.click()

        #wait for the button to view tranfer data to be visible and clickable
        viewTranferCourseBtn = WebDriverWait(assistDriver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'btn-primary'))
        )
        assistDriver.execute_script("arguments[0].scrollIntoView(true);", viewTranferCourseBtn)
        time.sleep(2)
        WebDriverWait(assistDriver, 10).until(
            EC.element_to_be_clickable(viewTranferCourseBtn)
        )
        viewTranferCourseBtn.click()
        
        self.getTransferData(assistDriver)

    def getTransferData(self, assistDriver) -> None:
        #giving the website 5 seconds to load before attempting to read from it
        time.sleep(5)

        with open('C:\wamp64\www\ChatbotAPI\majors.txt', 'r') as majors:
            for major in majors:
                #Wait for the search bar to load in before attempting to type in it
                search = WebDriverWait(assistDriver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ng-valid"))
                )
                search.send_keys(major)

                #wait for department options to load before trying to click on it
                department = WebDriverWait(assistDriver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "viewByRowColText"))
                )
                print(department.text)
                department.click()

                #wait for the sections tag to load before trying to read from it
                section = WebDriverWait(assistDriver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "template"))
                )
                
                #Get all the cc classes and their corresponding DH course
                divs = section.find_elements(By.XPATH, './div')
                for div in divs:
                    try:
                        classContainer = div.find_element(By.TAG_NAME, 'awc-template-requirement-group')
                        classPair = classContainer.find_element(By.CLASS_NAME, 'rowContent').find_elements(By.XPATH, './div')

                        #get class info and write to json
                        for pair in classPair:
                            #get info from csudh class
                            DHCourse = pair.find_element(By.CLASS_NAME, 'rowReceiving')
                            DHCourseNum = DHCourse.find_element(By.CLASS_NAME, 'prefixCourseNumber').text
                            DHCourseName = DHCourse.find_element(By.CLASS_NAME, 'courseTitle').text
                            DHCourseUnits = DHCourse.find_element(By.CLASS_NAME, 'courseUnits').text

                            #get info from CC class
                            ccCourse = pair.find_element(By.CLASS_NAME, 'rowSending')
                            ccCourseNum = ccCourse.find_element(By.CLASS_NAME, 'prefixCourseNumber').text
                            ccCourseName = ccCourse.find_element(By.CLASS_NAME, 'courseTitle').text
                            ccCourseUnits = ccCourse.find_element(By.CLASS_NAME, 'courseUnits').text

                            print(f"(CSUDH){DHCourseNum} {DHCourseName} {DHCourseUnits} units <- (cerritos college){ccCourseNum} {ccCourseName} {ccCourseUnits} units\n")
                    except NoSuchElementException:
                        continue

                search.clear()

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