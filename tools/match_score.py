from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent  
from langchain_community.document_loaders import PyPDFLoader
from langchain.messages import HumanMessage
import pandas as pd

from prompts import compare_cv_job


load_dotenv()

cv_path = r'data\CV_simple.pdf'
loader = PyPDFLoader(cv_path)
cv_doc = loader.load()

jb = pd.read_csv(r'linkedin_jobs_scout.csv')

def get_match_score(cv_doc, tit, jb_desc, comp_desc):

    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.8)

    agent = create_agent(
        model=llm,
        system_prompt=compare_cv_job)
    
    message = HumanMessage(content=f'Here is my CV:{cv_doc} and here is title:{tit}, job description: {jb_desc} and company description {comp_desc}.')
    
    response = agent.invoke({'messages': [message]})

    return response['messages'][-1].content[0]['text']

results = []
for index, row in jb.iterrows():
    analysis = get_match_score(cv_doc, row['job_title'], row['job_description'], row['company_info'])
    results.append(analysis)

jb['match_analysis'] = results
jb.to_csv("final_ranked_jobs.csv", index=False)