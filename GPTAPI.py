from flask import Flask, json, jsonify, request
from datetime import datetime
import threading
import schedule
import time
import sys
import os
sys.path.append(os.path.dirname(__file__))
from WebScraper import WebScraper

app = Flask(__name__)
scraper = WebScraper()

def scrapeJobData():
    print("Scraping job data...")
    scraper.scrapeJobs()

def scrapeCourseTransfers():
    print("Scraping course transfer data...")
    scraper.scrapeAssist()

def runSchedule():
    print("Starting schedule...")
    # This function runs the schedule in a loop
    while True:
        schedule.run_pending()
        time.sleep(1)  # Prevent excessive CPU usage

@app.route('/')
def root():
    return 'API TEST'

@app.route('/generateJobInfo', methods = ['GET'])
def generateJobInfo():
    scraper.scrapeJobs()

    with open('jobs.json', 'r') as file:
        jobs = json.load(file)
    return jsonify(jobs)

@app.route('/getJobInfo', methods = ['GET'])
def getJobInfo():
    with open('jobs.json', 'r') as file:
        jobs = json.load(file)
    return jsonify(jobs)

@app.route('/getCourseTransfers', methods=['GET'])
def getAssist():
    with open('transferdata.json', 'r') as file:
        courses = json.load(file)
    return courses
    
@app.route('/generateCourseTransfers', methods=['GET'])
def generateAssist():
    #if not scraper.hasScrapedAssist():
    scraper.scrapeAssist()

    with open('transferdata.json', 'r') as file:
        courses = json.load(file)
    return courses

application = app
if __name__ == '__main__':
    # Initialize the scraper
    scraper.initialize()

    # Schedule tasks
    schedule.every().day.at("00:00").do(scrapeJobData) #scrape job data every day at midnight
    schedule.every(10).seconds.do(scrapeCourseTransfers)

    # Start the scheduling in a new thread
    schedule_thread = threading.Thread(target=runSchedule)
    schedule_thread.daemon = True  # Ensures thread will close when the main program exits
    schedule_thread.start()
    app.run(debug=True, use_reloader=False)