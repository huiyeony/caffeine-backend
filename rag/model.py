# # 2. 임베딩 설정 (음료 검색의 눈 담당)
# # bge-m3 모델의 Ollama 버전입니다. 
# # 기존 FlagEmbedding 라이브러리 대신 LangChain 인터페이스로 깔끔하게 통합됩니다.
# from core.config import settings
# from langchain_ollama import ChatOllama
# from langchain_ollama import OllamaEmbeddings
# embeddings = OllamaEmbeddings(
#     model="bge-m3:567m", 
#     base_url=settings.OLLAMA_BASE_URL
# )
# llm = ChatOllama(model="coolsoon/kanana-1.5-8b", 
#                  temperature = 0 ,
#                  timeout=60,
#                  base_url="http://ollama:11434")


from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")