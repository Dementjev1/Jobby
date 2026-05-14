import logging

import os
import agentql
from playwright.sync_api import sync_playwright
from agentql.tools.sync_api import create_browser_session, paginate
from dotenv import load_dotenv

load_dotenv()

# Professional Practice: Configure the API Key
agentql.configure(api_key=os.getenv("AGENTQL_API_KEY"))

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


LOGGING_QUERY = """
{
    email_or_username
    password
    login_button

}
"""

JOB_SEARCH_QUERY = """
{ 
    search_input
}
"""

SEE_OPTIONS_QUERY = """
{
    options[] {option_name}
}
"""

JOB_QUERY = """
{
    jobs[] {
        job_name
    }
}
"""

JOB_SCRAP = """
{
    job_title
    company_name
    location
    description_text[] {unfold_description_button_link}
}
"""

URL = r'https://www.linkedin.com/login/?trk=guest_homepage-basic_nav-header-signin'

job_list = []

with sync_playwright() as p, p.chromium.launch(headless=False) as browser:
    page = agentql.wrap(browser.new_page())
    page.goto(URL)

    try:
        response = page.query_elements(LOGGING_QUERY)
        response.email_or_username.type("nikita.dementjev.vv@gmail.com", delay=75)
        response.password.type("Thenbhd2200", delay=75)
        response.login_button.click()

        page.wait_for_timeout(3000)  # Wait for 3 seconds to ensure the page has loaded after login

        response = page.query_elements(JOB_SEARCH_QUERY)
        response.search_input.type("Data Scientist", delay=75)
        
        response = page.query_elements(SEE_OPTIONS_QUERY)
        response.options[0].option_name.click()

        page.wait_for_timeout(3000)  # Wait for 3 seconds to ensure the page has loaded after clicking on Jobs

        response = page.query_elements(JOB_QUERY)
        for jb in response.jobs:
            jb.job_name.click()
            page.wait_for_timeout(2000)

            rp = page.query_data(JOB_SCRAP)
            job_list.append({
                "job_title": rp['job_title'],
                "company_name": rp['company_name'],
                "location": rp['location'],
                "description_text": rp['description_text']
            })

            if len(job_list) >= 5:  # Limit to the first 5 job postings for demonstration
                break

        print(job_list)
        # response = page.query_data(JOB_QUERY)
        # for job in response['jobs']:
        #     print(job['title'], job['company'], job['location'], job['description_text'])

    except Exception as e:
        print(f"An error occurred: {e}")