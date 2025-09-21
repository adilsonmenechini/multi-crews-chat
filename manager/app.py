import re
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv
import os

load_dotenv()

os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
os.environ['OTEL_SDK_DISABLED'] = 'true'

model = os.getenv("OLLAMA_MODEL")
base_url = os.getenv("OLLAMA_BASE_URL")

llm = LLM(model=model, base_url=base_url)

app = FastAPI()
logging.basicConfig(level=logging.INFO)

class Message(BaseModel):
    text: str

def safe_post(url: str, payload: dict, timeout: int = 60):
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()["result"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro chamando {url}: {e}")
        raise HTTPException(status_code=502, detail=f"Serviço indisponível: {url}")

def call_pesquisa(topic: str):
    result = safe_post("http://crew_pesquisa:8000/kickoff", {"inputs": {"topic": topic}})
    return result["raw"] if isinstance(result, dict) and "raw" in result else result

def call_redacao(topic: str, pesquisa: str):
    result = safe_post("http://crew_redacao:8000/kickoff", {"inputs": {"topic": topic, "pesquisa": pesquisa}})
    return result["raw"] if isinstance(result, dict) and "raw" in result else result

def call_avaliacao(artigo: str):
    result = safe_post("http://crew_avaliacao:8000/kickoff", {"inputs": {"artigo": artigo}})
    return result["raw"] if isinstance(result, dict) and "raw" in result else result

router_agent = Agent(
    role="Gerente de Conversa",
    goal="Decidir qual micro-crew chamar",
    backstory="Você coordena três assistentes: pesquisador, redator e avaliador.",
    verbose=False,
    memory=True,
    llm=llm
)

route_task = Task(
    description=(
        "Analise a mensagem: {message}. "
        "Responda APENAS com UMA das seguintes palavras exatas: "
        "pesquisa, redacao, avaliacao. "
        "Não adicione pontuação, aspas ou explicações."
    ),
    expected_output="Uma única palavra: pesquisa OU redacao OU avaliacao",
    agent=router_agent
)

manager_crew = Crew(
    agents=[router_agent],
    tasks=[route_task],
    process=Process.sequential,
    manager_llm=llm
)


VALID_DECISIONS = {"pesquisa", "redacao", "avaliacao"}

def parse_decision(raw: str) -> str | None:
    if not raw:
        return None
    decision = raw.strip().lower()
    decision = re.sub(r'[^a-z]', '', decision)
    return decision if decision in VALID_DECISIONS else None


@app.post("/chat")
def chat(msg: Message):
    result = manager_crew.kickoff(inputs={"message": msg.text})
    logging.info(f"Raw decision: '{result.raw}'")
    
    decision = parse_decision(result.raw)
    if not decision:
        return JSONResponse(content={"reply": f"Não consegui decidir. Recebi: '{result.raw}'"})
    
    actions = {
        "pesquisa": lambda: f"[Pesquisa] {call_pesquisa(msg.text)}",
        "redacao": lambda: f"[Redação] {call_redacao(msg.text, call_pesquisa(msg.text))}",
        "avaliacao": lambda: f"[Avaliação] {call_avaliacao(msg.text)}"
    }
    
    resposta = actions[decision]()
    return JSONResponse(content={"reply": resposta})