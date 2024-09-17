from flask import Flask, json, jsonify, request
import sys
import os
sys.path.append(os.path.dirname(__file__))
from WebScraper import WebScraper

app = Flask(__name__)
scraper = WebScraper()
assist = WebScraper(setOptions=False)

@app.route('/')
def root():
    return 'API TEST'

@app.route('/getJobInfo', methods = ['GET'])
def getJobInfo():
    if not scraper.hasScraped():
        scraper.scrapeJobs()

    with open('C:/wamp64/www/ChatbotAPI/jobs.json', 'r') as file:
        jobs = json.load(file)
    return jsonify(jobs)

@app.route('/courseTransfers', methods=['GET'])
def testAssist():
    assist.scrapeAssist()
    return "in testAssist"

application = app
if __name__ == '__main__':
    app.run(debug=True)