import logging
import re

import os
import agentql
from playwright.sync_api import sync_playwright
from agentql.tools.sync_api import create_browser_session, paginate
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# Professional Practice: Configure the API Key
agentql.configure(api_key=os.getenv("AGENTQL_API_KEY"))

# logging.basicConfig(level=logging.DEBUG)
# log = logging.getLogger(__name__)


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

        page.wait_for_timeout(2000)  # Wait for 3 seconds to ensure the page has loaded after login

        response = page.query_elements(JOB_SEARCH_QUERY)
        response.search_input.type("Financial analyst", delay=75)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

        page.get_by_role("radio", name="Filter by Jobs").click()

        page.wait_for_timeout(1000)  # Wait for 3 seconds to ensure the page has loaded after clicking on Jobs

        limit = 5

        for _ in range(4):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(500)

        # 1. Target the main column
        column = page.get_by_test_id("lazy-column")

        # 2. Get the buttons, but ONLY those that are actual job cards
        # We do this by looking for the 'componentkey' attribute which only jobs have
        job_cards = column.locator('div[role="button"][componentkey^="job-card"]').all()

        count = 0

        for card in job_cards:
            if count >= limit:
                break

            try:
                raw_text = card.inner_text().strip()
                
                # Take the first line (usually the title)
                if not raw_text or raw_text.isdigit() or len(raw_text) < 3:
                    continue
                    
                # LinkedIn titles are usually the first line
                lines = raw_text.split('\n')
                raw_title = lines[0]
                
                # Clean "Verified job" and whitespace
                clean_title = re.sub(r"\s*\(\text{Verified job}\)", "", raw_title, flags=re.IGNORECASE).strip()

                # 4. CLICK the card to update the side panel
                # We use force=True because LinkedIn's div-soup often overlaps
                card.click(force=True)
                page.wait_for_timeout(2000) # Wait for description to load

                text_boxes = page.get_by_test_id("expandable-text-box").all()
                
                job_desc = text_boxes[0].inner_text() if len(text_boxes) >= 1 else "N/A"
                comp_info = text_boxes[1].inner_text() if len(text_boxes) >= 2 else "N/A"

                # 6. Store it
                job_list.append({
                    "job_title": clean_title,
                    "job_description": job_desc,
                    "company_info": comp_info
                })
                
                print(f"✅ Scraped [{count+1}]: {clean_title}")
                count += 1

            except Exception as e:
                print(f"⚠️ Skipping a card due to error: {e}")
                continue
        
        # Convert your list of dictionaries to a DataFrame
        df = pd.DataFrame(job_list)

        # Export to CSV
        df.to_csv("linkedin_jobs_scout.csv", index=False, encoding='utf-8')
        print("✅ Exported to linkedin_jobs_scout.csv")

            # # Find the button that is INSIDE the job description section
            # page.locator("section", has_text="About the job").get_by_role("button", name="...more").click()

            # # Find the button that is INSIDE the company section
            # page.locator("section", has_text="About the company").get_by_role("button", name="...more").click()
            # page.wait_for_timeout(3000)


            # elements = page.query_elements(EXPAND_QUERY)
    
            # # Click job 'more' if it exists
            # if elements.about_the_job.show_more_job_btn:
            #     elements.about_the_job.show_more_job_btn.click()
            #     page.wait_for_timeout(3000) # Wait for expansion animation
                
            # # Click company 'more' if it exists
            # if elements.show_more_company_btn:
            #     elements.show_more_company_btn.click()
            #     page.wait_for_timeout(1000)

            # # Step 2: Get the actual text
            # print("Scraping expanded content...")
            # data = page.query_data(JOB_DATA_QUERY)
            # job_list.append({
            #     "job_title": data.job_details.title,
            #     "about_job_text": data.job_details.about_job_text,
            #     "about_company_text": data.job_details.about_company_text
            # })
            # if len(job_list) >= 1:  # Limit to the first 5 job postings for demonstration
            #     break

        #     rp = page.query_data(JOB_SCRAP)
        #     job_list.append({
        #         "job_title": rp['job_title'],
        #         "company_name": rp['company_name'],
        #         "location": rp['location'],
        #         "description_text": rp['description_text']
        #     })



        # print(job_list)
        # response = page.query_data(JOB_QUERY)
        # for job in response['jobs']:
        #     print(job['title'], job['company'], job['location'], job['description_text'])

    except Exception as e:
        print(f"An error occurred: {e}")