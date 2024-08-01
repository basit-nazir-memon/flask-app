from flask import Flask, jsonify
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json
import random

app = Flask(__name__)

def extract_data(soup):
    data = []
    job_tile_list = soup.find('div', {'data-test': 'job-tile-list'})
    if job_tile_list:
        job_tiles = job_tile_list.find_all('section', {'data-ev-sublocation': 'job_feed_tile'}, recursive=False)
        for job_tile in job_tiles:
            postedOn = job_tile.find('span', {'data-test': 'posted-on'}).text.strip() if job_tile.find('span', {'data-test': 'posted-on'}) else None
            title = job_tile.find('a', {'class': 'air3-link text-decoration-none'}).text.strip() if job_tile.find('a', {'class': 'air3-link text-decoration-none'}) else None
            type = job_tile.find('strong', {'data-test': 'job-type'}).text.strip() if job_tile.find('strong', {'data-test': 'job-type'}) else None
            budget = job_tile.find('span', {'data-test': 'budget'}).text.strip() if job_tile.find('span', {'data-test': 'budget'}) else None
            description = job_tile.find('span', {'data-test': 'job-description-text'}).text.strip() if job_tile.find('span', {'data-test': 'job-description-text'}) else None
            items = [item.text.strip() for item in job_tile.find_all('a', {'data-test': 'attr-item'})]
            proposals = job_tile.find('strong', {'data-test': 'proposals'}).text.strip() if job_tile.find('strong', {'data-test': 'proposals'}) else None
            payment_status = job_tile.find('small', {'data-test': 'payment-verification-status'}).text.strip() if job_tile.find('small', {'data-test': 'payment-verification-status'}) else None
            rating = job_tile.find('div', {'class': 'air3-rating air3-rating-sm'}).find('span', class_='sr-only').text.strip().split(' ')[2] if job_tile.find('div', {'class': 'air3-rating air3-rating-sm'}) else None
            spendings = job_tile.find('small', {'data-test': 'client-spendings'}).text.strip().split(' ')[0].strip() if job_tile.find('small', {'data-test': 'client-spendings'}) else None
            country = job_tile.find('small', {'data-test': 'client-country'}).text.strip().split('\n')[-1].strip() if job_tile.find('small', {'data-test': 'client-country'}) else None

            if postedOn:
                data.append({
                    'postedOn': postedOn,
                    'title': title,
                    'type': type,
                    'budget': budget,
                    'description': description,
                    'items': items,
                    'payment_status': payment_status,
                    'rating': rating,
                    'spendings': spendings,
                    'country': country,
                    'proposals': proposals,
                })
            else:
                print("No Data Posted Entry Found")
    return data

def filter_criteria(job):
    posted_within_last_day = "minutes ago" in job['postedOn'] or "1 hour ago" in job['postedOn']
    payment_verified = "Payment verified" in job.get('payment_status', "")
    spendings = job['spendings']
    if spendings.endswith('K+'):
        spendings_value = float(spendings[1:-2]) * 1000
    elif spendings.endswith('+'):
        spendings_value = float(spendings[1:-1])
    else:
        spendings_value = float(spendings[1:])
    rating = float(job['rating'])
    proposals = job['proposals']
    proposals_meet_criteria = proposals in ["Less than 5", "5 to 10", "10 to 15"]
    return posted_within_last_day and payment_verified and rating >= 4 and spendings_value >= 500 and proposals_meet_criteria

@app.route('/scrape', methods=['GET'])
def scrape():
    driver = None
    try:
        # Initialize Chrome options
        # options = Options()
        # options.headless = True

        # Initialize the undetected-chromedriver with options
        driver = uc.Chrome()

        # Load credentials from config file
        with open('config.json') as config_file:
            config = json.load(config_file)

        email = config['email']
        password = config['password']

        # Open a website
        driver.get('https://www.upwork.com/ab/account-security/login')

        # Wait for results to load
        time.sleep(random.randint(10, 20))

        try:
            accept_cookie_btn = driver.find_element(By.ID, 'onetrust-accept-btn-handler')
            if accept_cookie_btn:
                accept_cookie_btn.click()
            time.sleep(random.randint(1, 2))
        except:
            print("No cookie acceptance button found, continuing...")

        time.sleep(random.randint(1, 2))

        email_field = driver.find_element(By.XPATH, '//input[@type="text"]')
        email_field.send_keys(email)
        time.sleep(random.randint(1, 3))
        email_field.send_keys(Keys.RETURN)

        time.sleep(random.randint(3, 5))

        password_field = driver.find_element(By.XPATH, '//input[@type="password"]')
        password_field.send_keys(password)
        time.sleep(random.randint(1, 3))
        password_field.send_keys(Keys.RETURN)

        time.sleep(random.randint(4, 7))

        try:
            profile_modal = driver.find_element(By.CSS_SELECTOR, '[data-test="complete-your-profile-modal"]')
            if profile_modal:
                profile_button = driver.find_element(By.CSS_SELECTOR, '[class="air3-btn air3-btn-primary"]')
                if profile_button:
                    profile_button.click()
        except:
            print("No profile modal button found, continuing...")

        body = driver.find_element(By.TAG_NAME, 'body')
        for _ in range(10):
            body.send_keys(Keys.END)
            time.sleep(2)

        time.sleep(random.randint(4, 7))
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')
        data = extract_data(soup)

        # Optionally filter the data
        # filtered_data = [job for job in data if filter_criteria(job)]

        # Prepare JSON response
        response = json.dumps(data, indent=2, ensure_ascii=False)

        # Send response
        return jsonify(data), 200

    except Exception as e:
        return str(e), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(debug=True)
