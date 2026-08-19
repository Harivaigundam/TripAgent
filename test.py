from tools.tavily_tool import tavily_search
from tools.flight_tool_backup import flight_tool
from Backend import run_travel
# res = tavily_search("Best 4 star hotels in Chennai city")
# print(res)

# res1 = flight_tool("delhi to chennai", limit=1, )
# print(res1)

user_input = input("Enter your travel request: ")
response = run_travel(
    user_input=user_input,
    thread_id="test_user"
)

print("Final Response: \n\n")
print(response["answer"])