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

from pipeline import JobPipeline

job = JobPipeline(cv_path='data\CV_simple.pdf', search_keyword='Data Scientist')

job.run_pipeline()