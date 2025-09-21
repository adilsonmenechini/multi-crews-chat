from crewai.tools import tool
from duckduckgo_search import DDGS

@tool("duckduckgo_search")
def duckduckgo_search_tool(query: str) -> str:
    """
    Pesquisa no DuckDuckGo e retorna os top resultados como texto.
    
    Args:
        query (str): Termo de busca.
    
    Returns:
        str: Lista formatada com título e link dos resultados.
    """
    try:
        results_text = []
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=3, region="pt-br",)
            for r in results:
                title = r.get("title", "Sem título")
                href = r.get("href", "")
                body = r.get("body", "")
                results_text.append(f"- {title}\n  {href}\n  {body}")
        
        if not results_text:
            return "Nenhum resultado encontrado."
        
        return "\n\n".join(results_text)

    except Exception as e:
        return f"Erro ao buscar no DuckDuckGo: {str(e)}"