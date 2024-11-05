from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome
import logging
import json
import time
import os

class WebScraper:
    # Class variables
    service = None
    options = None
    jobDriver = None
    assistDriver = None

    @classmethod
    def initialize(cls):
        # Create an instance of ChromeDriverManager(CDM) to install CDM if it is not detected
        logging.basicConfig(level=logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        chrome = ChromeDriverManager(driver_version="125.0.6422.141")
        cls.service = Service(chrome.install())

        #Server doesn't have a display so we don't need to see an open instance of chrome unless we need it for testing purposes
        cls.options = Options()
        cls.options.add_argument('--no-sandbox')
        cls.options.add_argument('--headless')
        cls.options.add_argument('--disable-dev-shm-usage')
        cls.options.add_argument('--disable-gpu')
        cls.options.add_argument('--remote-debugging-port=9222')

        #Class attributes
        cls.jobDriver = Chrome(options=cls.options)
        cls.assistDriver = Chrome(options=cls.options)

        logging.info(f"Chrome binary located at: {cls.service.path}")

    @classmethod
    def scrapeJobs(cls) -> None:
        root = "https://www.governmentjobs.com"
        pgNum = 1
        jobs = []

        #loop through every page that has job information
        while True:
            url = root + f"/careers/lacity?page={pgNum}"
            cls.jobDriver.get(url)

            #Ensures html isn't parsed until the tags we need are rendered
            WebDriverWait(cls.jobDriver, 10).until(
                EC.any_of(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, 'item-details-link')),
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'not-found-text'))))

            #break out of the loop if the page has no jobs left
            if cls.containsChildByClass(cls.jobDriver, 'not-found-text'): break

            #loop through all the job data and add their info to a json file
            for job in cls.jobDriver.find_elements(By.CLASS_NAME, 'list-item'):
                link = job.find_element(By.TAG_NAME, 'a').get_attribute('href')
                jName = job.find_element(By.TAG_NAME, 'a').text
                specifics = job.find_element(By.TAG_NAME, 'ul').text
                jobs.append({
                    'Job Title': jName,
                    'Link': link,
                    'specifics': specifics
                })

            pgNum += 1
        cls.jobDriver.quit()
        with open('jobs.json', 'w') as file:
            json.dump(jobs, file, indent=4)

    '''
    @classmethod
    def hasCurrentYearAggreement(cls) -> bool:
        url = "https://assist.org"
        cls.assistDriver.get(url)

        try:
            cls.assistDriver.find_element(By.CLASS_NAME, 'agreement-year')
        except NoSuchElementException:
            return True
        return False
    '''
    
    @classmethod
    def scrapeAssist(cls) -> None:
        url = "https://assist.org"
        cls.assistDriver.get(url)
        transferData = {}
        
        with open('schools.txt', 'r') as schools:
            for school in schools:
                logging.info(f"Scraping {school}")
                #wait for the search bar to load before entering 'CSUDH' into the search bar
                logging.info(f"Waiting for selection box...")
                WebDriverWait(cls.assistDriver, 10).until(
                    EC.presence_of_element_located((By.ID, "governing-institution-select"))).send_keys('CSUDH')

                #wait for the CSUDH option to load from the dropdown menu before clicking on it
                logging.info(f"Waiting for csudh element...")
                WebDriverWait(cls.assistDriver, 10).until(
                    EC.presence_of_element_located((By.ID, 'option-202'))).click()

                #wait for the search bar to load before entering a CC institution
                logging.info(f"Waiting for institution agreement box...")
                try:
                    ccSearchBar = WebDriverWait(cls.assistDriver, 20).until(
                        EC.element_to_be_clickable((By.NAME, 'institution-agreement')))
                    logging.info("The element is now clickable.")

                except TimeoutException:
                    if cls.assistDriver.find_elements(By.NAME,'institution-agreement'):
                        logging.error("The element was found but not clickable")
                    else:
                        logging.error("The element was not found within the provided timeout")
                    raise

                #type the school we want tranfer class data from and then click on the 1st option from the drop down menu
                ccSearchBar.send_keys(school)
                schoolList = WebDriverWait(cls.assistDriver, 10).until(
                    EC.presence_of_element_located((By.ID, 'cdk-overlay-1')))
                
                school = schoolList.find_element(By.TAG_NAME, 'amc-option')
                schoolName = school.text[6:]
                transferData[schoolName] = {}
                school.click()

                #wait for the button to view tranfer data to be visible and clickable
                viewTranferCourseBtn = WebDriverWait(cls.assistDriver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'btn-primary')))
                
                cls.assistDriver.execute_script("arguments[0].scrollIntoView(true);", viewTranferCourseBtn)
                time.sleep(2)

                WebDriverWait(cls.assistDriver, 10).until(EC.element_to_be_clickable(viewTranferCourseBtn))
                viewTranferCourseBtn.click()

                cls.jsonifyTransferData(cls.assistDriver, transferData[schoolName])

        with open('transferdata.json', 'w') as json_file:
            json.dump(transferData, json_file, indent=4)

    @classmethod
    def jsonifyTransferData(cls, school) -> None:
        #giving the website 5 seconds to load before attempting to read from it
        time.sleep(3)

        header = WebDriverWait(cls.assistDriver, 10).until(
            EC.presence_of_element_located((By.ID, 'view-agreement-by')))

        with open('majors.txt', 'r') as majors:
            for major in majors:
                try:
                    #Wait for the search bar to load in before attempting to type in it
                    search = WebDriverWait(cls.assistDriver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "ng-valid")))
                    search.send_keys(major)

                    #wait for department options to load before trying to click on it
                    department = WebDriverWait(cls.assistDriver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "viewByRowColText")))
                    school[department.text] = []
                    department.click()

                except Exception as e:
                    #if department doesn't exist, clear the search bar to input the next department
                    search.clear()
                    continue

                #wait for the sections tag to load before trying to read from it
                section = WebDriverWait(cls.assistDriver, 15).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "template")))

                #Get all the cc classes and their corresponding DH course
                divs = section.find_elements(By.XPATH, './div')
                for div in divs:
                    try:
                        classContainer = div.find_element(
                            By.TAG_NAME, 'awc-template-requirement-group')
                        
                        classPair = classContainer.find_element(
                            By.CLASS_NAME,
                            'rowContent').find_elements(By.XPATH, './div')

                        #get class info and write to json
                        for pair in classPair:
                            #get info from csudh class
                            DHCourse = pair.find_element(
                                By.CLASS_NAME, 'rowReceiving')
                            #get info from cc class
                            ccCourse = pair.find_element(
                                By.CLASS_NAME, 'rowSending')

                            if cls.containsChildByClass(
                                    DHCourse, 'bracketContent'):
                                DHbracketContent = DHCourse.find_element(
                                    By.CLASS_NAME, 'bracketContent')
                                CCbracketContent = ccCourse.find_element(
                                    By.CLASS_NAME, 'bracketContent')
                                cls.handleMultiplePaths(
                                    DHbracketContent, CCbracketContent,
                                    school[department.text])
                            else:
                                cls.extractTransferData(
                                    DHCourse, ccCourse,
                                    school[department.text])

                    except NoSuchElementException:
                        continue

                search.clear()

        assistLogo = WebDriverWait(cls.assistDriver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'a')))
        cls.assistDriver.execute_script("arguments[0].click();", assistLogo)
        time.sleep(1)

    @staticmethod
    def handleMultiplePaths(DHbracket, CCbracket, major) -> None:
        DHcourses = DHbracket.find_elements(By.CLASS_NAME, 'courseLine')
        CCcourse = CCbracket.find_elements(By.CLASS_NAME, 'courseLine')
        DHStringBuilder = []
        CCStringBuilder = []

        for course in DHcourses:
            DHStringBuilder.append(course.text)
            DHStringBuilder.append('and')

        for course in CCcourse:
            CCStringBuilder.append(course.text)
            CCStringBuilder.append('and')

        DHStringBuilder.pop()
        CCStringBuilder.pop()

        major.append({
            'cc_course': {
                'multipleCourses': ' '.join(CCStringBuilder)
            },
            'dh_course': {
                'multipleCourses': ' '.join(DHStringBuilder)
            }
        })

    @staticmethod
    def extractTransferData(DHCourse, ccCourse, transferData) -> None:
        DHCourseNum = DHCourse.find_element(By.CLASS_NAME, 'prefixCourseNumber').text
        DHCourseName = DHCourse.find_element(By.CLASS_NAME, 'courseTitle').text
        DHCourseUnits = DHCourse.find_element(By.CLASS_NAME, 'courseUnits').text

        #if a community college doesn't have a class that transfers to the necessary class at DH, then add that to the  json
        if ccCourse.text == "No Course Articulated":
            transferData.append({
                'cc_course': {
                    'comment': 'No Course Articulated'
                },
                'dh_course': {
                    'number': DHCourseNum,
                    'name': DHCourseName,
                    'units': DHCourseUnits
                }
            })
        #otherwise, add the corresponding class to the json
        else:
            ccCourseNum = ccCourse.find_element(By.CLASS_NAME, 'prefixCourseNumber').text
            ccCourseName = ccCourse.find_element(By.CLASS_NAME, 'courseTitle').text
            ccCourseUnits = ccCourse.find_element(By.CLASS_NAME, 'courseUnits').text

            transferData.append({
                'cc_course': {
                    'number': ccCourseNum,
                    'name': ccCourseName,
                    'units': ccCourseUnits
                },
                'dh_course': {
                    'number': DHCourseNum,
                    'name': DHCourseName,
                    'units': DHCourseUnits
                }
            })

    @staticmethod
    def containsChildByClass(parent, child) -> bool:
        try:
            parent.find_element(By.CLASS_NAME, child)
        except NoSuchElementException:
            return False
        return True