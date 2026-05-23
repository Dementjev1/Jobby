from unittest import loader

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader

from playwright.sync_api import sync_playwright
import agentql
import os
import re
import pandas as pd

from tools.prompts import compare_cv_job

load_dotenv()



# Define the function as an official LangChain tool
class JobPipeline:
    def __init__(self, cv_path: str, search_keyword: str):
        loader = PyPDFLoader(cv_path)
        self.cv_doc = "\n".join([doc.page_content for doc in loader.load()])
        self.search_keyword = search_keyword
        self.intermediate_results = None
        self.comparison_results = None
        self.url = r'https://www.linkedin.com/login/?trk=guest_homepage-basic_nav-header-signin'
        self.LOGGING_QUERY = """
        {
            email_or_username
            password
            login_button

        }
        """
        self.JOB_SEARCH_QUERY = """
        { 
            search_input
        }
        """

        agentql.configure(api_key=os.getenv("AGENTQL_API_KEY"))
    def job_scrapper(self):
        '''

        Method to scrape LinkedIn for job postings based on the search keyword. It logs in, performs the search, and extracts job titles, descriptions, and company info.
        args: search_keyword (str): The job title or keyword to search for on LinkedIn.
        args: url (str): The LinkedIn login URL.
        returns: Dataframe added to the SQL database with the scraped job information: position_name, company_name, job_description.
        
        '''

        agentql.configure(api_key=os.getenv("AGENTQL_API_KEY"))

        job_list = []

        with sync_playwright() as p, p.chromium.launch(headless=False) as browser:
                page = agentql.wrap(browser.new_page())
                page.goto(self.url)

                try:
                    #Logging into linkedin account
                    response = page.query_elements(self.LOGGING_QUERY)
                    response.email_or_username.type("nikita.dementjev.vv@gmail.com", delay=75)
                    response.password.type("Thenbhd2200", delay=75)
                    response.login_button.click()

                    page.wait_for_timeout(2000)  # Wait for 3 seconds to ensure the page has loaded after login

                    link_ = "https://www.linkedin.com/jobs/"
                    page.goto(link_)
                    page.wait_for_timeout(2000)

                    #Searching for the job using position keyword
                    response = page.query_elements(self.JOB_SEARCH_QUERY)
                    response.search_input.type(self.search_keyword, delay=75)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(1000)

                    # Maximum number of jobs to scrape
                    limit = 4

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
                    df.to_csv("linkedin_jobs_scout.csv", index=False, encoding='utf-8')
                    print("✅ Exported to linkedin_jobs_scout.csv")

                    self.intermediate_results = df

                except Exception as e:
                        print(f"An error occurred: {e}")

    def evaluate_job_fit(self,agent, row) -> str:
        """
        Evaluates how well a candidate's CV aligns with a specific job posting. 
        It computes a match score, flags key skill gaps, and gives an application verdict.

        Args:
            cv_doc (str): The full text copy of the candidate's CV or Resume.
            row (pd.Series): A row from the DataFrame containing the job listing information.

        Returns:
            str: A generated evaluation containing a match score, missing skills/gaps, and an entry verdict.
        """
        # 1. Initialize your specific model inside the tool scope

        
        # 3. Format structural clean spacing for the text block payloads
        message = HumanMessage(
            content=f"Here is my CV:\n{self.cv_doc}\n\n"
                    f"Target Job Title:\n{row.job_title}\n\n"
                    f"Job Description:\n{row.job_description}\n\n"
                    f"Company Profile:\n{row.company_info}"
        )
        
        # 4. Invoke evaluation workflow
        response = agent.invoke({'messages': [message]})
        
        # 5. Extract output string safely handling either standard strings or structure blocks
        last_msg = response['messages'][-1]
        if isinstance(last_msg.content, list):
            return last_msg.content[0].get('text', str(last_msg.content[0]))
        return str(last_msg.content)


    def run_pipeline(self):
        
        self.job_scrapper()

        llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.8)

        # 2. Spawn the sub-agent specialized in matching
        agent = create_agent(
            model=llm,
            system_prompt=self.cv_doc
        )

        for row in self.intermediate_results.itertuples():
            evaluation = self.evaluate_job_fit(agent, row)
            print(f"Evaluation for {row.job_title}:\n{evaluation}\n{'-'*50}\n")
        
