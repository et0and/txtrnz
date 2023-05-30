from flask import Flask, render_template
from bs4 import BeautifulSoup
import requests
import json
import os
import time
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)

data = []  # Hold our scraped data

def scrape_rnz():
    global data
    url = 'https://rnz.co.nz'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Clear old data
    data = []

    # Scrape new data
    items = soup.select('.o-digest')
    for item in items:
        headline_elem = item.select_one('.o-digest__headline')
        summary_elem = item.select_one('.o-digest__summary')
        link_elem = item.select_one('.u-blocklink .faux-link')

        # Only proceed if all elements were found
        if headline_elem and summary_elem and link_elem:
            headline = headline_elem.text
            summary = summary_elem.text
            link = url + link_elem['href']

            # Scrape article page
            time.sleep(2)  # wait for 2 seconds to avoid being blocked
            article_response = requests.get(link)
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            article_text = []
            for selector in ['.article__body p', '.episode-body p', '.page__body p']:
                elements = article_soup.select(selector)
                for element in elements:
                    article_text.append(element.text)

            data.append({'Headline': headline, 'Summary': summary, 'URL': link, 'ArticleText': article_text})

    # Write data to a JSON file
    with open('rnz_data.json', 'w') as f:
        json.dump(data, f)


@app.route('/')
def home():
    # Check if the JSON file exists
    if os.path.exists('rnz_data.json'):
        # Read data from a JSON file
        with open('rnz_data.json') as f:
            data = json.load(f)

        # Generate today's date
        today = datetime.now().strftime('%B %d, %Y')

        # Render data to the HTML template
        return render_template('homepage.html', data=data, today=today)
    else:
        # Render a placeholder page
        return "Data is being prepared. Please try again in a few minutes."


@app.route('/article/<int:article_id>')
def article(article_id):
    # Check if the JSON file exists
    if os.path.exists('rnz_data.json'):
        # Read data from a JSON file
        with open('rnz_data.json') as f:
            data = json.load(f)

        if article_id < len(data):
            # Generate today's date
            today = datetime.now().strftime('%B %d, %Y')

            # Render data to the HTML template
            return render_template('article.html', article=data[article_id], today=today)
        else:
            return "Article not found.", 404
    else:
        # Render a placeholder page
        return "Data is being prepared. Please try again in a few minutes."


# Run scrape_rnz once at start to ensure that JSON file is created
scrape_rnz()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scrape_rnz, 'interval', hours=1)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
