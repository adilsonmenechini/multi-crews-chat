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

avaliador = Agent(
    role="Crítico Literário",
    goal="Avaliar clareza e qualidade de artigos",
    backstory="Você dá feedback construtivo em textos.",
    verbose=False,
    memory=False,
    llm=llm
)

avaliacao_task = Task(
    description="Avalie o artigo recebido: {artigo}.",
    expected_output="Parecer crítico de 1 parágrafo com feedback.",
    agent=avaliador
)

crew = Crew(agents=[avaliador], tasks=[avaliacao_task], process=Process.sequential)

@app.post("/kickoff")
def kickoff(data: Input):
    return {"result": crew.kickoff(inputs=data.inputs)}
