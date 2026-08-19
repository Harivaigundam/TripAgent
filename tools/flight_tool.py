import os
import re
import json
import certifi
from dotenv import load_dotenv

from tavily import TavilyClient


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


# ============================================================
# CONFIGURATION
# ============================================================

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is missing from .env file."
    )


# ============================================================
# TAVILY CLIENT
# ============================================================

tavily_client = TavilyClient(
    api_key=TAVILY_API_KEY
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:

    if not text:
        return ""

    text = str(text).strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# PARSE ROUTE
# ============================================================

def parse_route(query: str):

    if not query:
        return None, None

    query = clean_text(query)

    patterns = [

        # Chennai to Delhi
        r"(.+?)\s+to\s+(.+)",

        # Chennai -> Delhi
        r"(.+?)\s*->\s*(.+)",

        # Chennai - Delhi
        r"(.+?)\s*-\s*(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query,
            re.IGNORECASE
        )

        if match:

            origin = clean_text(
                match.group(1)
            )

            destination = clean_text(
                match.group(2)
            )

            return origin, destination

    return None, None


# ============================================================
# REMOVE DUPLICATE RESULTS
# ============================================================

def remove_duplicate_results(results):

    unique = []

    seen = set()

    for result in results:

        url = result.get(
            "url",
            ""
        )

        title = result.get(
            "title",
            ""
        )

        key = (
            url.lower().strip()
            if url
            else title.lower().strip()
        )

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)

        unique.append(result)

    return unique


# ============================================================
# SEARCH FLIGHTS USING TAVILY
# ============================================================

def search_flights(
    origin: str,
    destination: str,
    max_results: int = 10
):

    if not origin:

        return {
            "success": False,
            "error": "Origin is required."
        }

    if not destination:

        return {
            "success": False,
            "error": "Destination is required."
        }


    # ========================================================
    # SEARCH QUERIES
    # ========================================================

    queries = [

        f"{origin} to {destination} flights",

        f"flights from {origin} to {destination}",

        f"{origin} {destination} flight schedule",

    ]


    all_results = []


    # ========================================================
    # EXECUTE TAVILY SEARCH
    # ========================================================

    try:

        for query in queries:

            response = tavily_client.search(

                query=query,

                search_depth="advanced",

                topic="general",

                max_results=max_results,

                include_answer=True,

                include_raw_content=False
            )

            results = response.get(
                "results",
                []
            )

            all_results.extend(
                results
            )


        # ====================================================
        # REMOVE DUPLICATES
        # ====================================================

        all_results = remove_duplicate_results(
            all_results
        )


        # ====================================================
        # LIMIT RESULTS
        # ====================================================

        all_results = all_results[
            :max_results
        ]


        # ====================================================
        # CREATE CLEAN RESULTS
        # ====================================================

        flights = []

        for result in all_results:

            flights.append({

                "title": result.get(
                    "title",
                    ""
                ),

                "url": result.get(
                    "url",
                    ""
                ),

                "content": result.get(
                    "content",
                    ""
                ),

                "score": result.get(
                    "score",
                    None
                )
            })


        # ====================================================
        # TAVILY ANSWER
        # ====================================================

        answer_parts = []

        try:

            response_answer = response.get(
                "answer"
            )

            if response_answer:

                answer_parts.append(
                    response_answer
                )

        except Exception:

            pass


        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "success": True,

            "source": "Tavily Web Search",

            "data_type": (
                "web_searched_flight_information"
            ),

            "route": {

                "origin": origin,

                "destination": destination
            },

            "count": len(
                flights
            ),

            "summary": "\n\n".join(
                answer_parts
            ),

            "flights": flights,

            "important_notice": (
                "Flight information was "
                "retrieved from web search. "
                "This does not guarantee live "
                "seat availability, booking "
                "availability, or ticket price."
            )
        }


    # ========================================================
    # TAVILY ERROR
    # ========================================================

    except Exception as ex:

        return {

            "success": False,

            "source": "Tavily Web Search",

            "error": (
                "Unable to retrieve "
                "flight information "
                "from Tavily."
            ),

            "details": str(ex)
        }


# ============================================================
# MAIN FLIGHT TOOL
# ============================================================

def flight_tool(
    query: str,
    limit: int = 10
):

    # ========================================================
    # VALIDATION
    # ========================================================

    if not query:

        return {

            "success": False,

            "error": (
                "Flight search query "
                "cannot be empty."
            )
        }


    # ========================================================
    # PARSE ROUTE
    # ========================================================

    origin, destination = parse_route(
        query
    )


    if not origin or not destination:

        return {

            "success": False,

            "error": (
                "Could not understand "
                "the flight route."
            ),

            "example": (
                "Chennai to Delhi"
            )
        }


    # ========================================================
    # SEARCH
    # ========================================================

    return search_flights(

        origin=origin,

        destination=destination,

        max_results=limit
    )


# ============================================================
# LOCAL TEST
# ============================================================

# if __name__ == "__main__":

#     print(
#         "\n"
#         "========================================\n"
#         " TAVILY FLIGHT TOOL TEST\n"
#         "========================================\n"
#     )


#     test_queries = [

#         "Chennai to Delhi",

#         "Delhi to Mumbai",

#         "Bangalore to Chennai",

#     ]


#     for query in test_queries:

#         print(
#             f"\nSearching: {query}"
#         )

#         result = flight_tool(
#             query,
#             limit=5
#         )

#         print(
#             json.dumps(
#                 result,
#                 indent=2,
#                 ensure_ascii=False
#             )
#         )


#     print(
#         "\n========================================"
#     )