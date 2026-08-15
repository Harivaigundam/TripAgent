from tools.tavily_tool import tavily_search
from tools.flight_tool import flight_tool

# res = tavily_search("Best 4 star hotels in Chennai city")
# print(res)

res1 = flight_tool("delhi to chennai", limit=1, )
print(res1)