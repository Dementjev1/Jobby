import logging
import re

import os
import agentql
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

agentql.configure(api_key=os.getenv("AGENTQL_API_KEY"))

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

def scrape_linkedin_jobs(position_name):
    with sync_playwright() as p, p.chromium.launch(headless=False) as browser:
        page = agentql.wrap(browser.new_page())
        page.goto(URL)

        try:
            response = page.query_elements(LOGGING_QUERY)
            response.email_or_username.type("nikita.dementjev.vv@gmail.com", delay=75)
            response.password.type("Thenbhd2200", delay=75)
            response.login_button.click()

            page.wait_for_timeout(2000)  # Wait for 3 seconds to ensure the page has loaded after login

            link_ = "https://www.linkedin.com/jobs/"

            page.goto(link_)
            page.wait_for_timeout(2000)

            response = page.query_elements(JOB_SEARCH_QUERY)
            response.search_input.type(position_name, delay=75)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)

            limit = 5

            for _ in range(4):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)

            # 1. Target the main column
            column = page.get_by_test_id("lazy-column")

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
                    clean_title = re.sub(r"\s*\(Verified job\)", "", raw_title, flags=re.IGNORECASE).strip()

                    card.click(force=True)
                    # 4. CLICK the card to update the side panel
                    # We use force=True because LinkedIn's div-soup often overlaps
                    link_element = page.get_by_role("link", name=clean_title)
                    link_element.first.click(force=True)
                    page.wait_for_timeout(2000) # Wait for description to load

                    text_boxes = page.get_by_test_id("expandable-text-box").all()

                    for box in text_boxes:
                        try:
                            # 2. Look for the "see more" or "...more" button inside the box
                            # LinkedIn often uses a button or a span with the text "...more" or "see more"
                            more_button = box.get_by_role("button", name=re.compile(r"more", re.I))
                            
                            # 3. If it's visible, click it
                            if more_button.is_visible():
                                more_button.click()
                                # Small wait for the animation/text to expand
                                page.wait_for_timeout(500)
                        except Exception:
                            # If no button is found, the text was already full—just move on
                            pass
                    
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

                    page.go_back()
                    page.wait_for_timeout(2000)

                except Exception as e:
                    print(f"⚠️ Skipping a card due to error: {e}")
                    continue
            
            # Convert your list of dictionaries to a DataFrame
            df = pd.DataFrame(job_list)

            # Export to CSV
            df.to_csv("linkedin_jobs_scout.csv", index=False, encoding='utf-8')
            print("✅ Exported to linkedin_jobs_scout.csv")

        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    position = "Human resources"
    scrape_linkedin_jobs(position)