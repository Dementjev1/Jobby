from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent  
from langchain_community.document_loaders import PyPDFLoader
from langchain.messages import HumanMessage

from prompts import compare_cv_job


load_dotenv()

cv_path = r'data\CV_simple.pdf'

def compare_cv(prompt=compare_cv_job):
    
    loader = PyPDFLoader(cv_path)
    cv_doc = loader.load()
    job_desc = """Product Builder Programme Ready to build the future of product in an AI-native world? We’re looking for recent graduates and ambitious, curious builders to join our next-generation Product Builder Program in Tallinn, Estonia. The 12-month program launches in September 2026, and you'll be invited to our on-site Recruitment Day at the Bolt office in early May if you're shortlisted. Please note: we’re not able to offer visa sponsorship or relocation support for this role, so make sure you’re all set to be in Estonia if you apply! What to expect from the hiring process: ● Quick video interview ● Face-to-face (online) interview with the Recruiter ● In-person Recruitment Day in Tallinn (think product tasks + interviews) If you're ready to dive into the world of product, we can’t wait to meet you! About us With over 200 million customers in 50+ countries, Bolt is one of the fastest-growing tech companies in Europe and Africa. And it's all thanks to our people. We believe in creating an inclusive environment where everyone is welcome, regardless of race, colour, religion, gender identity, sexual orientation, age, or disability. Our ultimate goal is to make cities for people, not cars, and we need your help to achieve this mission! About the program The graduate program is an annual initiative designed to attract and retain top early-career talent in product roles in Estonia. The 12-month program is designed to cultivate Product Builders: people who can design, build, and ship using AI as their primary leverage. Upon completion, you will graduate into a full-time Product role, equipping you with the skills and experience needed to drive impact within the organization. Main tasks and responsibilities ● Leverage AI for exponential output: use tools like Claude, ChatGPT, Cursor, and others to dramatically improve workflows and accelerate delivery. ● Impact: work in small teams to autonomously build, design, and launch both internal and external products. ● Collaborate cross-functionally: operate across product management, design, and engineering lines in order to build strong relationships. ● Experiment & Iterate: rapidly adopt new AI tools and methodologies, to incorporate user and stakeholder feedback and improve product outcomes fast. ● AI-native: Help define what product development looks like in an AI-native organization About you ● You're starting your journey in the Product space, and you're not looking for a traditional graduate role — you want to build, ship, and redefine how products are created in an AI-native world. ● You enjoy thinking about customer experience, building innovative products, and collaborating with engineering, design, and other disciplines. ● You have a curious and problem-solving mindset — you’re eager to learn, open to feedback, structured in your thinking, and thrive on solving challenges. ● You communicate and collaborate effectively — you're fluent in English, work well with cross-functional teams, and can articulate decisions clearly. Portfolio & Experience: ● You actively use AI tools like Claude, ChatGPT, Cursor, Copilot, v0, or Replit — and you’ve built real products that prove you don’t just experiment, you ship. ● You can build end-to-end products — comfortable across frontend and backend fundamentals — and you care deeply about design, UX, and the small details that make products feel great. Experience is great, but what we really look for is drive, intelligence, and integrity. So even if you don’t tick every box, please consider applying! Why you’ll love it here ● Play a direct role in shaping the future of mobility. ● Impact millions of customers and partners in 600+ cities across 50+ countries. ● Work in fast-moving autonomous teams with some of the smartest people in the world. ● Accelerate your professional growth with unique career opportunities. ● Get a rewarding salary and stock option package that lets you focus on doing your best work. ● Enjoy the flexibility of working in a hybrid mode with a minimum of 3 days in the office each week to foster strong connections and teamwork. ● Take care of your physical and mental health with our wellness perks. Some perks may differ depending on your location and role."""

    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.8)

    agent = create_agent(
        model=llm,
        system_prompt=prompt)
    
    message = HumanMessage(content=f'Here is my CV:{cv_doc} and here is the job description: {job_desc}.')
    
    response = agent.invoke({'messages': [message]})

    print(response['messages'][-1].content)


    