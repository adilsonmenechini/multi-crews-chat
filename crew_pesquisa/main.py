from fastapi import FastAPI
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from tool_ddgs import duckduckgo_search_tool
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

pesquisador = Agent(
    role="Pesquisador Acadêmico",
    goal="Encontrar informações confiáveis sobre o tópico solicitado",
    backstory="Você resume pontos relevantes de forma clara.",
    verbose=False,
    llm=llm,
    memory=False,
    tools=[duckduckgo_search_tool]
)

pesquisa_task = Task(
    description="Realize uma pesquisa completa sobre {topic}.",
    expected_output="Resumo claro e estruturado.",
    agent=pesquisador
)

crew = Crew(agents=[pesquisador], tasks=[pesquisa_task], process=Process.sequential)

@app.post("/kickoff")
def kickoff(data: Input):
    return {"result": crew.kickoff(inputs=data.inputs)}
