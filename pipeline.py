import multiprocessing
from unittest import loader

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader

from playwright.async_api import async_playwright
import agentql
import os
import re
import pandas as pd
import random
import json
import asyncio

from playwright.sync_api import sync_playwright

from tools.prompts import compare_cv_job
from database import SessionLocal, JobEvaluationModel, init_db

load_dotenv()



# Define the function as an official LangChain tool
class JobPipeline:
    def __init__(self, client_iddd: str, cv_text: str, search_keyword: str):
        self.client_id = client_iddd
        self.cv_doc = cv_text
        self.search_keyword = search_keyword
        self.url = f"https://www.linkedin.com/jobs/search?keywords={self.search_keyword}&location=Tallinn"
        self.results = None
        self.prompt = compare_cv_job

    def job_scrapper(self):
        '''

        Method to scrape LinkedIn for job postings based on the search keyword. It logs in, performs the search, and extracts job titles, descriptions, and company info.
        args: search_keyword (str): The job title or keyword to search for on LinkedIn.
        args: url (str): The LinkedIn login URL.
        returns: Dataframe added to the SQL database with the scraped job information: position_name, company_name, job_description.
        
        '''

        job_dct = {}
        job_links = {}

        def rdm():
            return random.uniform(1.5, 3) *1000

        with sync_playwright() as p, p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]) as browser:
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                                      locale="en-US")
                page = context.new_page()
            
                print(f"🌐 Navigating to Guest Feed: {self.url}")
                page.goto(self.url)

                dimensions = page.evaluate("""() => {
                    return {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                }""")
                
                # 2. Calculate the exact bottom-right coordinates
                # Subtracting 1 pixel to stay safely inside the clickable window boundary
                bottom_right_x = dimensions["width"] - 1
                bottom_right_y = dimensions["height"] - 1
                
                print(f"Clicking bottom-right corner at coordinates: ({bottom_right_x}, {bottom_right_y})")
                
                # 3. Direct the hardware mouse to click that exact location
                page.mouse.click(bottom_right_x, bottom_right_y)
                page.wait_for_timeout(rdm())  # Wait for 2 seconds to ensure the page has loaded after the click

                for _ in range(3):
                    page.mouse.wheel(0, 500)
                    page.wait_for_timeout(1000)

                count = 0
                limit = 8

                job_cards = page.locator("ul.jobs-search__results-list a.base-card__full-link").all()
                print(f"Found {len(job_cards)} job cards on the page.")

                for lk in job_cards:
                    if count >= limit:
                        break

                    try:
                        lk.click(force=True)
                        print('Reviewing job card...')

                        page.wait_for_timeout(rdm())
                        link_element = page.locator("a.topcard__link")
                        job_url = link_element.get_attribute("href")
                        clean_title = page.locator("h2.top-card-layout__title").inner_text().strip()
                        job_links[clean_title] = job_url

                        count+=1

                    except Exception as e:
                        print(f"⚠️ Skipping a card due to error: {e}")
                        continue

                print(job_links)

                context.close()

                for title, target_url in job_links.items():
                    
                    # If you want to keep track of progress or skip already scraped items:
                    if target_url in job_dct.keys():
                        print(f"⏭️ Skipping index {title}, already processed.")
                        continue

                    print(f"🔄 Processing job index [{title}] with a fresh context...")

                    # Spin up a brand new incognito context for this specific job URL
                    clean_context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        viewport={"width": 1024, "height": 768}
                    )
                    single_page = clean_context.new_page()

                    try:
                        # Navigating directly to the specific job view page
                        # This completely skips having to click the list card or the title header!
                        single_page.goto(target_url, wait_until="commit", timeout=15000)

                        single_page.wait_for_timeout(rdm())  # Wait for the page to load after navigation
                
                        
                        dimensions = single_page.evaluate("""() => {
                            return {
                                width: window.innerWidth,
                                height: window.innerHeight
                            }
                        }""")
                        
                        # 2. Calculate the exact bottom-right coordinates
                        # Subtracting 1 pixel to stay safely inside the clickable window boundary
                        bottom_right_x = dimensions["width"] - 1
                        bottom_right_y = dimensions["height"] - 1
                        
                        print(f"Clicking bottom-right corner at coordinates: ({bottom_right_x}, {bottom_right_y})")
                        
                        # 3. Direct the hardware mouse to click that exact location
                        single_page.mouse.click(bottom_right_x, bottom_right_y)


                        description_container = single_page.locator("div.show-more-less-html__markup")
                        # Capture everything inside it safely
                        full_description_text = description_container.inner_text().strip()
                            
                        print(f"✅ Successfully scraped index [{title}]")
                            
                            # Save to your tracked history
                        job_dct[title] = (full_description_text, target_url)
                        

                    except Exception as e:
                        print(f"⚠️ Error loading index {title}: {e}")
                        
                    finally:
                        # Destroy this environment entirely before moving to the next item
                        clean_context.close()
                self.results = job_dct
                return True

    def evaluate_job_fit(self, agent, title: str, description: str) -> dict | None:
        """
        Evaluates how well a candidate's CV aligns with a specific job posting. 
        It parses the AI's JSON output string and returns a structured dictionary.

        Args:
            agent: The LangChain agent or runnable instance.
            title (str): The title of the target job.
            description (str): The description of the target job.

        Returns:
            dict | None: The parsed AI evaluation data payload, or None if parsing fails.
        """
        
        # 1. Format structural clean spacing for the text block payloads
        # Note: Ensure the system prompt instructions we created are either part of the agent's 
        # system message or appended here to guarantee JSON format delivery.
        message = HumanMessage(
            content=f"Here is my CV:\n{self.cv_doc}\n\n"
                    f"Target Job Title:\n{title}\n\n"
                    f"Job Description:\n{description}\n\n"
        )
        
        # 2. Invoke evaluation workflow
        response = agent.invoke({'messages': [message]})
        
        # 3. Extract output string safely handling either standard strings or structure blocks
        last_msg = response['messages'][-1]


        if isinstance(last_msg.content, list):
            raw_content = last_msg.content[0].get('text', str(last_msg.content[0]))
        else:
            raw_content = str(last_msg.content)
            
        # Just return the raw text block exactly as the AI provided it!
        return raw_content
        
    

    async def run_pipeline(self):
        
        p = multiprocessing.Process(target=self.job_scrapper)
        p.start()
        
        # Use an executor to wait for the process to finish
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, p.join)
        
        init_db()

        llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.8)

        # 2. Spawn the sub-agent specialized in matching
        agent = create_agent(
            model=llm,
            system_prompt=self.prompt
                )
        for title, (desc, url) in self.results.items():
            # 1. Fetch the raw, unparsed string text from your AI agent function
            raw_ai_string = self.evaluate_job_fit(agent, title, desc)
            print(f"Evaluation text retrieved for {title}")
            
            db = SessionLocal()
            try:
                # 2. Clean the markdown wrappers and parse the JSON text into a Python dict
                clean_json_str = re.sub(r"^```json|```$", "", raw_ai_string.strip(), flags=re.MULTILINE).strip()
                data = json.loads(clean_json_str)

                # 3. Pull top-level fields with safe fallbacks
                extracted_title = data.get("job_title", title)
                extracted_company = data.get("company_name", "Unknown Company")
                extracted_location = data.get("location", "Remote")
                
                try:
                    extracted_score = int(data.get("match_score", 50))
                except (ValueError, TypeError):
                    extracted_score = 50

                # 4. 🛡️ DATA SHAPE DEFENSE
                # Convert arrays to flat strings just in case the AI ignores instructions
                raw_matching = data.get("matching_skills", "")
                matching_skills_str = ", ".join([str(x).strip() for x in raw_matching if x]) if isinstance(raw_matching, list) else str(raw_matching)

                raw_absent = data.get("absent_skills", "")
                absent_skills_str = ", ".join([str(x).strip() for x in raw_absent if x]) if isinstance(raw_absent, list) else str(raw_absent)

                raw_improvements = data.get("improvements", "")
                improvements_str = "\n".join([str(x).strip() for x in raw_improvements if x]) if isinstance(raw_improvements, list) else str(raw_improvements)

                # 5. Check database state to protect against identical entries (Duplicates)
                existing_record = db.query(JobEvaluationModel).filter(
                    JobEvaluationModel.scraped_url == url).first()
                
                if existing_record:
                    print(f"⏭️ [SKIP] '{extracted_title}' at '{extracted_company}' already exists in database. Skipping duplicate entry.")
                    continue  # Move onto the next job description in the results dict
                
                # 6. Map elements to the 8 clean, flat database columns
                new_record = JobEvaluationModel(
                    user_id=self.client_id,
                    search_keyword=self.search_keyword,
                    job_title=extracted_title,
                    company_name=extracted_company,
                    location=extracted_location,
                    match_score=extracted_score,
                    matching_skills=matching_skills_str,
                    absent_skills=absent_skills_str,
                    fit_analysis=data.get("fit_analysis", ""),
                    improvements=improvements_str,
                    scraped_url=url  # Map your active scraper URL state parameter here
                )
                
                # 7. Commit permanently to SQLite storage
                db.add(new_record)
                db.commit()
                print(f"💾 [SUCCESS] Safely loaded and indexed: {extracted_title} at {extracted_company}")
                
            except json.JSONDecodeError as json_err:
                print(f"🚨 [JSON FORMAT ERROR] AI outputted unparsable formatting: {json_err}")
                print(f"Raw context block was:\n{raw_ai_string}")
            except Exception as e:
                db.rollback()
                print(f"❌ [DATABASE ERROR] Failed to process flat record layout: {e}")
            finally:
                db.close()
        return True