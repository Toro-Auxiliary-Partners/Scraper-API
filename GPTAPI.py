import threading
import logging
import time
import sys
import os
sys.path.append(os.path.dirname(__file__))
from WebScraper import WebScraper

def scrapeJobData():
    logging.info("Scraping job data...")
    scraper.scrapeJobs()

def scrapeCourseTransfers():
    logging.info("Scraping course transfer data...")
    scraper.scrapeAssist()

def scrapeData():
    #currTime = time.localtime()

    scrapeJobData()

    #if currTime.tm_mday % 6 == 0:
        #assistThread.start()

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

    # Initialize the scraper
    scraper = WebScraper()
    scraper.initialize()

    # Start the scheduling in a new thread
    assistThread = threading.Thread(target=scrapeCourseTransfers, daemon=True)  # Ensures thread will close when the main program exits
    logging.info("Assist thread created.")

    scrapeData()