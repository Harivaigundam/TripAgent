import os
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from tools.tavily_tool import tavily_search
from typing import TypedDict, Annotated
import operator
import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    AnyMessage
)
from langchain_groq import ChatGroq
from tools.flight_tool_backup import flight_tool
from tools.tavily_tool import tavily_search

def get_database_url():
    db_url= os.getenv("DATABASE_URL")
    
    if not db_url:
        raise ValueError("DB URL is missing. please add your Render PostgreSQL")
    
    if "sslmode" not in db_url:
        seperator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{seperator}sslmode=require"
        
    return db_url

# url=get_database_url()
# print(url)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("MODEL")
if not GROQ_API_KEY:
    raise ValueError("GROQ API Key is missing")

#LLM Client Creation
llm = ChatGroq(
    model=MODEL,
    api_key=GROQ_API_KEY
)

#State creation
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_result:str
    hotel_result: str
    itinerary: str
    llm_calls: str


#flight Agent

def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = flight_tool(query)
    
    return {
        "flight_result": flight_data,
        "messages" :[
            AIMessage(content="Flight results fetched.")
        ],
        "llm_calls": state.get("llm_calls", 0) +1
    }
    
def hotel_agent(state:TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_result = tavily_search(query)

    return {
        "hotel_result" : hotel_result,
        "messages" : [AIMessage(content="Hotel information Fetched.")],
        "llm_calls" : state.get("llm_calls", 0) + 1
    }
    

#Itinerary Agent
def itinerary_agent(state: TravelState):
    prompt = f"""
create a complete travel itinerary.
user query:
{state.get('user_query')}

Flight Results: {state.get('flight_result')}

Hotel Results: {state.get('hotel_result')}
Make the itinerary practical, budget aware and easy to follow.
    """
    response = llm.invoke([
        SystemMessage(content="you are an expert travel planner"),
        HumanMessage(content=prompt)
    ])
    
    return {
        "itinerary" : response.content,
        "messages" : [response],
        "llm_call" :state.get("llm_calls", 0) + 1
    }
    
def final_agent (state:TravelState):
    final_prompt = f"""
generate the final response for the user
user Request:
{state.get('user_query')}

Flights: {state.get('flight_result')}

Hotels: {state.get('hotel_result')}

Itinerary: {state.get('itinerary')}

Format: concise, friendly, and actionable.
Formaat the final beautifully using these sections:
1.Trip Summar
2. Flight Information
3. Hotel suggestions
4. Day by Day Itinerary
5. estimate Budget
6. Final Recommendations

Important:
-Be clear and pratical
-mention that live flight api may not provide ticket prices if pricing is unavailable
-Keep the response useful for real travel planning.
    """
    response = llm.invoke([
        SystemMessage(content="You are an expert assistant composing a clear final reply."),
        HumanMessage(content=final_prompt)
    ])

    return {
        "final_response": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


#build the graph
graph = StateGraph(TravelState)

graph.add_node("flight", flight_agent)
graph.add_node("hotel", hotel_agent)
graph.add_node("Itinerary", itinerary_agent)
graph.add_node("final", final_agent)

#wiring - edges
graph.add_edge(START, "flight")
graph.add_edge("flight", "hotel")
graph.add_edge("hotel", "Itinerary")
graph.add_edge("Itinerary", "final")
graph.add_edge("final", END)

#create a checkpointer
DATABASE_URL = get_database_url()

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

#pass checkpointer into graph
travel_graph = graph.compile(checkpointer=checkpointer)

#function for fast api
def run_travel (user_input:str, thread_id:str | None = None):
    if not thread_id:
        thread_id = f"user{uuid.uuid4().hex}"
    
    config = {
        "configurable" :{
            "thread_id": thread_id
        }
    }
    
    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query" : user_input,
            "flight_result": "",
            "hotel_result": "",
            "itinerary":"",
            "llm_calls":0
        },
        config=config
    )
    
    final_answer = result["messages"][-1].content
    
    return{
        "thread_id":thread_id,
        "answer": final_answer,
        "flight_result": result.get("flight_result", ""),
        "hotel_result" : result.get("hotel_result", ""),
        "itinerary": result.get("itinerary",""),
        "llm_calls": result.get("llm_calls", 0)
    }