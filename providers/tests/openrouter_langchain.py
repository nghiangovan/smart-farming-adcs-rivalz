from dotenv import load_dotenv
import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

openai_api_key = os.getenv('OPENROUTER_API_KEY')
openai_api_base = os.getenv('OPENROUTER_API_BASE')

if not openai_api_key:
    raise ValueError("OPENROUTER_API_KEY is not set in the environment.")
if not openai_api_base:
    raise ValueError("OPENROUTER_API_BASE is not set in the environment.")

template = """Question: {question}
Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])

llm = ChatOpenAI(
    model_name="openai/gpt-4o-mini",
    openai_api_key=openai_api_key,
    openai_api_base=openai_api_base,
    temperature=0.7,
)

chain = prompt | llm

question = "What NFL team won the Super Bowl in the year Justin Bieber was born?"

result = chain.invoke({"question": question})

print(result)
