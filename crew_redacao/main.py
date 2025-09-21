from fastapi import FastAPI
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv
import os

load_dotenv()

os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
os.environ['OTEL_SDK_DISABLED'] = 'true'

model = os.getenv("OLLAMA_MODEL")
base_url = os.getenv("OLLAMA_BASE_URL")

llm = LLM(
    model=f"{model}",
    base_url=f"{base_url}"
)

app = FastAPI()

class Input(BaseModel):
    inputs: dict

redator = Agent(
    role="Redator Criativo",
    goal="Transformar pesquisas em artigos envolventes",
    backstory="Você escreve de forma acessível e atrativa.",
    verbose=False,
    memory=False,
    llm=llm
)

redacao_task = Task(
    description="Escreva um artigo sobre {topic} baseado na pesquisa: {pesquisa}",
    expected_output="Artigo de 3 parágrafos bem escrito.",
    agent=redator
)

crew = Crew(agents=[redator], tasks=[redacao_task], process=Process.sequential)

@app.post("/kickoff")
def kickoff(data: Input):
    return {"result": crew.kickoff(inputs=data.inputs)}
