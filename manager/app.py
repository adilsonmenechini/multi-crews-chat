from fastapi import FastAPI
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

llm = LLM(
    model=f"{model}",
    base_url=f"{base_url}"
)

app = FastAPI()

class Message(BaseModel):
    text: str

def call_pesquisa(topic: str):
    r = requests.post("http://crew_pesquisa:8000/kickoff", json={"inputs": {"topic": topic}}, timeout=60)
    return r.json()["result"]

def call_redacao(topic: str, pesquisa: str):
    r = requests.post("http://crew_redacao:8000/kickoff", json={"inputs": {"topic": topic, "pesquisa": pesquisa}}, timeout=60)
    return r.json()["result"]

def call_avaliacao(artigo: str):
    r = requests.post("http://crew_avaliacao:8000/kickoff", json={"inputs": {"artigo": artigo}}, timeout=60)
    return r.json()["result"]

router_agent = Agent(
    role="Gerente de Conversa",
    goal="Entender a mensagem do usuário e decidir qual micro-crew deve ser chamado",
    backstory="Você coordena três assistentes: pesquisador, redator e avaliador.",
    verbose=False,
    memory=True,
    llm=llm
)

route_task = Task(
    description="Analise a mensagem: {message}. Responda APENAS com UMA das seguintes palavras exatas: pesquisa, redacao, avaliacao. Não adicione pontuação, aspas ou explicações.",
    expected_output="Uma única palavra: pesquisa OU redacao OU avaliacao",
    agent=router_agent
)

manager_crew = Crew(
    agents=[router_agent],
    tasks=[route_task],
    process=Process.sequential,
    manager_llm=llm
)

@app.post("/chat")
def chat(msg: Message):
    result = manager_crew.kickoff(inputs={"message": msg.text})
    print(f"Raw decision: '{result.raw}'")  # Debug line
    
    decision = result.raw.strip().lower()
    decision = decision.replace('"', '').replace("'", '').replace('.', '').strip()
    print(f"Cleaned decision: '{decision}'")  # Debug line
    
    if decision == "pesquisa":
        resposta = call_pesquisa(msg.text)
        return {"reply": f"[Pesquisa] {resposta}"}
    elif decision == "redacao":
        pesquisa = call_pesquisa(msg.text)
        resposta = call_redacao(msg.text, pesquisa)
        return {"reply": f"[Redação] {resposta}"}
    elif decision == "avaliacao":
        resposta = call_avaliacao(msg.text)
        return {"reply": f"[Avaliação] {resposta}"}
    
    return {"reply": f"Não consegui decidir. Recebi: '{decision}'"}