# from data.seed import seed_initial_data
from data.seed import seed_initial_data
from rag.promps import CAFFEINE_GUIDE_PROMPT
from rag.tool import search_caffeine_by_brands
from core.database import init_db
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
# from rag.model import llm # 기존 로컬 모델 임포트 주석 처리
from langchain_openai import ChatOpenAI # OpenAI 연동 모듈 추가

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 시작 시 DB 상태 확인 및 테이블 생성
    init_db()
    await seed_initial_data() #<-- await 없으면 실행 안됨 
    
    print(">>> [API] Server started")
    
    yield
    print(">>> [API] Server shutdown, Scheduler stopped.")
    
app = FastAPI(lifespan=lifespan)

# 1. CORS 설정 (프론트엔드 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. openai API 연결 및 도구 바인딩
# OpenAI 모델 객체 초기화 (gpt-4o-mini 또는 gpt-4o 지정 가능)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools([search_caffeine_by_brands])

@app.get("/ask")
async def ask_caffeine(q: str = Query(...)):

    # STEP 1: 메시지 리스트 초기화
    messages = [
        SystemMessage(content=CAFFEINE_GUIDE_PROMPT),
        HumanMessage(content=q)
    ]
    
    # STEP 2: 첫 번째 요청 (키워드 추출 및 도구 호출)
    ai_msg = await llm_with_tools.ainvoke(messages)
    
    # STEP 3: DB 검색 수행
    if ai_msg.tool_calls:
        # LLM의 호출 요청 메시지를 히스토리에 추가
        messages.append(ai_msg)
        # 첫번째 지시 : 메가커피 아이스아메리카노 
        # 두번째 지시 : 메가커피 할메가리카노 
        # 세번째 지시 : ..
        for tool_call in ai_msg.tool_calls:
            # STEP 3: 즉시 DB 검색 실행 및 결과 저장
            search_result = await search_caffeine_by_brands.ainvoke(tool_call)
            
            # [핵심] 검색 결과를 ToolMessage로 만들어 히스토리에 추가 (LLM에게 Context 제공)
            messages.append(ToolMessage(
                content=str(search_result), 
                tool_call_id=tool_call["id"]
            ))
        
        # STEP 4: 데이터(Context)가 포함된 전체 히스토리를 가지고 LLM에게 최종 답변 요청
        final_response = await llm_with_tools.ainvoke(messages)
        return {"answer": final_response.content}
    
    # 도구 호출 없이 직접 답변 가능한 경우 (예: "안녕")
    return {"answer": ai_msg.content}