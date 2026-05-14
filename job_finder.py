import os
import agentql
from playwright.sync_api import sync_playwright
from agentql.tools.sync_api import create_browser_session, paginate
from dotenv import load_dotenv

load_dotenv()

# Professional Practice: Configure the API Key
agentql.configure(api_key=os.getenv("AGENTQL_API_KEY"))

JOB_QUERY = """
{
    jobs[] {
        title
        company
        location
        description_text
    }
}
"""

URL = r'https://www.cvkeskus.ee/toopakkumised?op=search&search%5Bjob_salary%5D=3&ga_track=results&search%5Blocations%5D%5B%5D=3&search%5Bkeyword%5D=Data+scientist&badge%5Bjob_lang%5D=on&search%5Bexpires_days%5D=&search%5Bjob_lang%5D=en&search%5Bsalary%5D='

with sync_playwright() as p, p.chromium.launch(headless=False) as browser:
    page = agentql.wrap(browser.new_page())
    page.goto(URL)

    try:
        response = page.query_data(JOB_QUERY)
        for job in response['jobs']:
            print(job['title'], job['company'], job['location'], job['description_text'])

    except Exception as e:
        print(f"An error occurred: {e}")