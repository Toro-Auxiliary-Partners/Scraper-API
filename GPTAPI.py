from flask import Flask, json, jsonify, request
import sys
import os
sys.path.append(os.path.dirname(__file__))
from WebScraper import WebScraper

app = Flask(__name__)
scraper = WebScraper()
assist = WebScraper()

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
    assist.scrapeAssist()

    with open('transferdata.json', 'r') as file:
        courses = json.load(file)
    return courses

application = app
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)