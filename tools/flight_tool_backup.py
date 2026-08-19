import os
import re
import json
import certifi
import requests

from dotenv import load_dotenv
import airportsdata
import pycountry


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

DEFAULT_ORIGIN_DATA = os.getenv(
    "DEFAULT_ORIGIN_DATA",
    "MAA"
)

BASE_URL = "https://api.aviationstack.com/v1/flights"


if not API_KEY:
    raise ValueError(
        "AVIATIONSTACK_API_KEY is missing from .env file."
    )


# ============================================================
# LOAD AIRPORT DATA
# ============================================================

airports = airportsdata.load("IATA")


# ============================================================
# COUNTRY ALIASES
# ============================================================

COUNTRY_ALIASES = {

    "usa": "US",
    "america": "US",
    "united states": "US",
    "united states of america": "US",

    "uk": "GB",
    "england": "GB",
    "united kingdom": "GB",

    "uae": "AE",
    "emirates": "AE",

    "india": "IN",
    "bharat": "IN",

    "srilanka": "LK",
    "sri lanka": "LK",

    "bangladesh": "BD",
    "pakistan": "PK",
    "nepal": "NP",
    "malaysia": "MY",
    "singapore": "SG",
    "thailand": "TH",
    "vietnam": "VN",
    "indonesia": "ID",
    "philippines": "PH",
    "myanmar": "MM",
    "cambodia": "KH",
    "laos": "LA",
    "brunei": "BN",
    "maldives": "MV",
}


# ============================================================
# MAIN AIRPORT BY COUNTRY
# ============================================================

COUNTRY_MAIN_AIRPORTS = {

    "BD": "DAC",
    "US": "JFK",
    "IN": "DEL",
    "PK": "ISB",
    "LK": "CMB",
    "NP": "KTM",
    "MY": "KUL",
    "SG": "SIN",
    "TH": "BKK",
    "VN": "SGN",
    "ID": "CGK",
    "PH": "MNL",
    "MM": "RGN",
    "KH": "PNH",
    "LA": "VTE",
    "BN": "BWN",
    "MV": "MLE",

    "AF": "KBL",
    "IR": "IKA",
    "SA": "RUH",
    "AE": "DXB",
    "OM": "MCT",
    "QA": "DOH",
    "KW": "KWI",
    "BH": "BAH",
    "IL": "TLV",
    "TR": "IST",
    "EG": "CAI",
    "DZ": "ALG",
}


# ============================================================
# MAIN AIRPORT BY CITY
# ============================================================

CITY_MAIN_AIRPORTS = {

    # USA
    "new york": "JFK",
    "los angeles": "LAX",
    "chicago": "ORD",
    "houston": "IAH",
    "miami": "MIA",
    "san francisco": "SFO",
    "atlanta": "ATL",
    "dallas": "DFW",
    "boston": "BOS",
    "seattle": "SEA",
    "washington": "DCA",

    # India
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "hyderabad": "HYD",
    "pune": "PNQ",
    "kochi": "COK",
    "cochin": "COK",
    "ahmedabad": "AMD",
    "goa": "GOI",
    "coimbatore": "CJB",
    "trivandrum": "TRV",
    "thiruvananthapuram": "TRV",
    "madurai": "IXM",
    "tiruchirappalli": "TRZ",
    "trichy": "TRZ",
    "tirunelveli": "TRV",

    # Bangladesh
    "dhaka": "DAC",

    # Pakistan
    "islamabad": "ISB",
    "karachi": "KHI",
    "lahore": "LHE",

    # Sri Lanka
    "colombo": "CMB",

    # Nepal
    "kathmandu": "KTM",

    # Malaysia
    "kuala lumpur": "KUL",

    # Singapore
    "singapore": "SIN",

    # Thailand
    "bangkok": "BKK",

    # Vietnam
    "ho chi minh city": "SGN",
    "saigon": "SGN",

    # Indonesia
    "jakarta": "CGK",

    # Philippines
    "manila": "MNL",

    # Myanmar
    "yangon": "RGN",

    # Cambodia
    "phnom penh": "PNH",

    # Laos
    "vientiane": "VTE",

    # Brunei
    "bandar seri begawan": "BWN",

    # Maldives
    "male": "MLE",
}


# ============================================================
# TEXT CLEANING
# ============================================================

def cleaning_text(text: str) -> str:

    if not text:
        return ""

    text = str(text).lower().strip()

    # Replace punctuation with spaces
    text = re.sub(
        r"[^a-zA-Z0-9\s]",
        " ",
        text
    )

    # Remove multiple spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    stop_words = {

        "flights",
        "flight",
        "airline",
        "airlines",
        "airplane",
        "plane",
        "airport",
        "airports",
        "ticket",
        "tickets",
        "booking",
        "bookings",
        "reservation",
        "reservations",

        "from",
        "to",
        "in",
        "on",
        "at",
        "for",

        "the",
        "a",
        "an",

        "and",
        "or",
        "but",
        "if",
        "then",
        "else",

        "when",
        "where",
        "why",
        "how",
        "what",
        "which",
        "who",
        "whom",
        "whose",

        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",

        "have",
        "has",
        "had",

        "do",
        "does",
        "did",
    }

    words = [
        word
        for word in text.split()
        if word not in stop_words
    ]

    return " ".join(words).strip()


# ============================================================
# COUNTRY NAME -> ISO CODE
# ============================================================

def country_name_to_code(text: str):

    if not text:
        return None

    original_text = str(text).strip()

    cleaned = cleaning_text(
        original_text
    )

    # --------------------------------------------------------
    # Alias
    # --------------------------------------------------------

    if cleaned in COUNTRY_ALIASES:

        return COUNTRY_ALIASES[
            cleaned
        ]

    # --------------------------------------------------------
    # ISO Alpha-2
    # --------------------------------------------------------

    if len(cleaned) == 2:

        country = pycountry.countries.get(
            alpha_2=cleaned.upper()
        )

        if country:
            return country.alpha_2

    # --------------------------------------------------------
    # pycountry lookup
    # --------------------------------------------------------

    try:

        country = pycountry.countries.lookup(
            original_text
        )

        return country.alpha_2

    except LookupError:

        pass

    # --------------------------------------------------------
    # Search country name
    # --------------------------------------------------------

    for country in pycountry.countries:

        country_name = getattr(
            country,
            "name",
            ""
        ).lower()

        if (
            country_name
            and country_name in cleaned
        ):

            return country.alpha_2

        official_name = getattr(
            country,
            "official_name",
            ""
        ).lower()

        if (
            official_name
            and official_name in cleaned
        ):

            return country.alpha_2

        common_name = getattr(
            country,
            "common_name",
            ""
        ).lower()

        if (
            common_name
            and common_name in cleaned
        ):

            return country.alpha_2

    # --------------------------------------------------------
    # Alias search
    # --------------------------------------------------------

    for alias, code in COUNTRY_ALIASES.items():

        if alias in cleaned:

            return code

    return None


# ============================================================
# AIRPORT COUNTRY MATCH
# ============================================================

def airport_country_matches(
    airport_data,
    country_code
) -> bool:

    airport_country = str(
        airport_data.get(
            "country",
            ""
        )
    ).upper().strip()

    country_code = str(
        country_code
    ).upper().strip()

    if not airport_country:
        return False

    # Direct country code
    if airport_country == country_code:
        return True

    # Country name comparison
    try:

        country = pycountry.countries.get(
            alpha_2=country_code
        )

        if country:

            country_name = str(
                country.name
            ).lower()

            if (
                airport_country.lower()
                == country_name
            ):

                return True

    except Exception:

        pass

    return False


# ============================================================
# FIND BEST AIRPORT FOR COUNTRY
# ============================================================

def get_best_airport_for_country(
    country_code
):

    if not country_code:
        return None

    country_code = country_code.upper()

    # --------------------------------------------------------
    # Preferred airport
    # --------------------------------------------------------

    preferred_airport = (
        COUNTRY_MAIN_AIRPORTS.get(
            country_code
        )
    )

    if preferred_airport:

        return preferred_airport

    # --------------------------------------------------------
    # Find airport from airportsdata
    # --------------------------------------------------------

    candidate_airports = []

    for iata, airport in airports.items():

        if not iata or not airport:
            continue

        if airport_country_matches(
            airport,
            country_code
        ):

            name = str(
                airport.get(
                    "name",
                    ""
                )
            ).lower()

            city = str(
                airport.get(
                    "city",
                    ""
                )
            ).lower()

            score = 0

            if "international" in name:
                score += 50

            if "intl" in name:
                score += 40

            if city:
                score += 10

            candidate_airports.append(
                (
                    iata,
                    score
                )
            )

    if not candidate_airports:

        return None

    candidate_airports.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return candidate_airports[0][0]


# ============================================================
# RESOLVE LOCATION -> IATA
# ============================================================

def resolve_location_to_iata(
    location: str
):

    if not location:
        return None

    original = str(
        location
    ).strip()

    # --------------------------------------------------------
    # 1. Direct IATA code
    # --------------------------------------------------------

    if len(original) == 3:

        code = original.upper()

        if code in airports:

            return code

    # --------------------------------------------------------
    # 2. Clean text
    # --------------------------------------------------------

    cleaned = cleaning_text(
        original
    )

    # --------------------------------------------------------
    # 3. City mapping
    # --------------------------------------------------------

    if cleaned in CITY_MAIN_AIRPORTS:

        return CITY_MAIN_AIRPORTS[
            cleaned
        ]

    # --------------------------------------------------------
    # 4. Search airportsdata
    # --------------------------------------------------------

    for iata, airport in airports.items():

        if not iata or not airport:
            continue

        city = str(
            airport.get(
                "city",
                ""
            )
        ).lower().strip()

        name = str(
            airport.get(
                "name",
                ""
            )
        ).lower().strip()

        if cleaned == city:

            return iata

        if cleaned == name:

            return iata

    # --------------------------------------------------------
    # 5. Country
    # --------------------------------------------------------

    country_code = country_name_to_code(
        cleaned
    )

    if country_code:

        return get_best_airport_for_country(
            country_code
        )

    # --------------------------------------------------------
    # 6. Partial city/name search
    # --------------------------------------------------------

    for iata, airport in airports.items():

        city = str(
            airport.get(
                "city",
                ""
            )
        ).lower()

        name = str(
            airport.get(
                "name",
                ""
            )
        ).lower()

        if cleaned in city:

            return iata

        if cleaned in name:

            return iata

    return None


# ============================================================
# PARSE ROUTE
# ============================================================

def parse_route(
    route: str
):

    if not route:

        return None, None

    route = route.strip()

    patterns = [

        # Chennai to Delhi
        r"(.+?)\s+to\s+(.+)",

        # Chennai -> Delhi
        r"(.+?)\s*->\s*(.+)",

        # Chennai - Delhi
        r"(.+?)\s*-\s*(.+)",
    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            route,
            re.IGNORECASE
        )

        if match:

            origin = (
                match.group(1)
                .strip()
            )

            destination = (
                match.group(2)
                .strip()
            )

            return (
                origin,
                destination
            )

    return None, None


# ============================================================
# AVIATIONSTACK FLIGHT SEARCH
#
# FREE PLAN:
# Real-time flight data
#
# IMPORTANT:
# Do NOT send flight_date for this Free-plan tool.
# ============================================================

def search_flights(
    origin=None,
    destination=None,
    airline_iata=None,
    limit=20
):

    # --------------------------------------------------------
    # Default origin
    # --------------------------------------------------------

    if not origin:

        origin = DEFAULT_ORIGIN_DATA

    # --------------------------------------------------------
    # Resolve origin
    # --------------------------------------------------------

    origin_iata = (
        resolve_location_to_iata(
            origin
        )
    )

    if not origin_iata:

        return {
            "success": False,
            "error": (
                f"Unable to resolve "
                f"origin: {origin}"
            )
        }

    # --------------------------------------------------------
    # Destination required
    # --------------------------------------------------------

    if not destination:

        return {
            "success": False,
            "error": (
                "Destination is required."
            )
        }

    # --------------------------------------------------------
    # Resolve destination
    # --------------------------------------------------------

    destination_iata = (
        resolve_location_to_iata(
            destination
        )
    )

    if not destination_iata:

        return {
            "success": False,
            "error": (
                f"Unable to resolve "
                f"destination: {destination}"
            )
        }

    # --------------------------------------------------------
    # API PARAMETERS
    #
    # Keep this minimal for Free plan.
    # --------------------------------------------------------

    params = {

        "access_key": API_KEY,

        "dep_iata": origin_iata,

        "arr_iata": destination_iata,
    }

    # --------------------------------------------------------
    # Optional airline filter
    # --------------------------------------------------------

    if airline_iata:

        params[
            "airline_iata"
        ] = airline_iata

    # --------------------------------------------------------
    # LIMIT
    #
    # We don't send limit to avoid unnecessary
    # unsupported parameters.
    #
    # We apply it locally instead.
    # --------------------------------------------------------

    try:

        # ----------------------------------------------------
        # API REQUEST
        # ----------------------------------------------------

        response = requests.get(

            BASE_URL,

            params=params,

            timeout=30,

            verify=certifi.where()
        )

        # ----------------------------------------------------
        # Parse response
        # ----------------------------------------------------

        try:

            result = response.json()

        except ValueError:

            return {

                "success": False,

                "status_code": (
                    response.status_code
                ),

                "error": (
                    "Aviationstack returned "
                    "non-JSON response."
                ),

                "raw_response": (
                    response.text
                )
            }

        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            error_data = (
                result.get(
                    "error",
                    result
                )
            )

            error_code = None

            if isinstance(
                error_data,
                dict
            ):

                error_code = (
                    error_data.get(
                        "code"
                    )
                )

            # ------------------------------------------------
            # Subscription restriction
            # ------------------------------------------------

            if (
                response.status_code == 403
                and
                error_code
                == "function_access_restricted"
            ):

                return {

                    "success": False,

                    "status_code": 403,

                    "error": (
                        "Your Aviationstack "
                        "subscription does not "
                        "allow this API function."
                    ),

                    "aviationstack_code": (
                        error_code
                    ),

                    "details": error_data,

                    "hint": (
                        "This tool is configured "
                        "for the Free-plan "
                        "real-time flight endpoint. "
                        "Do not send flight_date, "
                        "future-date or schedule "
                        "parameters."
                    )
                }

            return {

                "success": False,

                "status_code": (
                    response.status_code
                ),

                "error": error_data,

                "raw_response": result
            }

        # ----------------------------------------------------
        # API-level error
        # ----------------------------------------------------

        if "error" in result:

            return {

                "success": False,

                "error": result["error"],

                "raw_response": result
            }

        # ----------------------------------------------------
        # Flight data
        # ----------------------------------------------------

        flights = result.get(
            "data",
            []
        )

        # Apply local limit
        if limit:

            flights = flights[
                :int(limit)
            ]

        clean_flights = []

        # ----------------------------------------------------
        # Process flights
        # ----------------------------------------------------

        for flight in flights:

            departure = (
                flight.get(
                    "departure",
                    {}
                ) or {}
            )

            arrival = (
                flight.get(
                    "arrival",
                    {}
                ) or {}
            )

            airline = (
                flight.get(
                    "airline",
                    {}
                ) or {}
            )

            flight_info = (
                flight.get(
                    "flight",
                    {}
                ) or {}
            )

            aircraft = (
                flight.get(
                    "aircraft",
                    {}
                ) or {}
            )

            # ------------------------------------------------
            # Clean flight object
            # ------------------------------------------------

            clean_flight = {

                "flight_number": (
                    flight_info.get(
                        "iata"
                    )
                ),

                "flight_number_icao": (
                    flight_info.get(
                        "icao"
                    )
                ),

                "airline": (
                    airline.get(
                        "name"
                    )
                ),

                "airline_iata": (
                    airline.get(
                        "iata"
                    )
                ),

                "status": (
                    flight.get(
                        "flight_status"
                    )
                ),

                "departure": {

                    "airport": (
                        departure.get(
                            "airport"
                        )
                    ),

                    "iata": (
                        departure.get(
                            "iata"
                        )
                    ),

                    "scheduled": (
                        departure.get(
                            "scheduled"
                        )
                    ),

                    "estimated": (
                        departure.get(
                            "estimated"
                        )
                    ),

                    "actual": (
                        departure.get(
                            "actual"
                        )
                    ),

                    "terminal": (
                        departure.get(
                            "terminal"
                        )
                    ),

                    "gate": (
                        departure.get(
                            "gate"
                        )
                    ),
                },

                "arrival": {

                    "airport": (
                        arrival.get(
                            "airport"
                        )
                    ),

                    "iata": (
                        arrival.get(
                            "iata"
                        )
                    ),

                    "scheduled": (
                        arrival.get(
                            "scheduled"
                        )
                    ),

                    "estimated": (
                        arrival.get(
                            "estimated"
                        )
                    ),

                    "actual": (
                        arrival.get(
                            "actual"
                        )
                    ),

                    "terminal": (
                        arrival.get(
                            "terminal"
                        )
                    ),

                    "gate": (
                        arrival.get(
                            "gate"
                        )
                    ),
                },

                "aircraft": {

                    "registration": (
                        aircraft.get(
                            "registration"
                        )
                    ),

                    "iata": (
                        aircraft.get(
                            "iata"
                        )
                    ),

                    "icao": (
                        aircraft.get(
                            "icao"
                        )
                    ),

                    "icao24": (
                        aircraft.get(
                            "icao24"
                        )
                    ),
                },

                "live": (
                    flight.get(
                        "live"
                    )
                ),
            }

            clean_flights.append(
                clean_flight
            )

        # ----------------------------------------------------
        # Final response
        # ----------------------------------------------------

        return {

            "success": True,

            "source": "Aviationstack",

            "data_type": (
                "real_time_flights"
            ),

            "route": {

                "origin": {
                    "input": origin,
                    "iata": origin_iata
                },

                "destination": {
                    "input": destination,
                    "iata": destination_iata
                }
            },

            "count": len(
                clean_flights
            ),

            "flights": clean_flights
        }

    # --------------------------------------------------------
    # Timeout
    # --------------------------------------------------------

    except requests.exceptions.Timeout:

        return {

            "success": False,

            "error": (
                "Aviationstack API "
                "request timed out."
            )
        }

    # --------------------------------------------------------
    # Connection error
    # --------------------------------------------------------

    except requests.exceptions.ConnectionError as ex:

        return {

            "success": False,

            "error": (
                "Could not connect to "
                "Aviationstack API."
            ),

            "details": str(ex)
        }

    # --------------------------------------------------------
    # Other request error
    # --------------------------------------------------------

    except requests.exceptions.RequestException as ex:

        return {

            "success": False,

            "error": (
                "HTTP request failed."
            ),

            "details": str(ex)
        }

    # --------------------------------------------------------
    # Unexpected error
    # --------------------------------------------------------

    except Exception as ex:

        return {

            "success": False,

            "error": (
                "Unexpected error occurred."
            ),

            "details": str(ex)
        }


# ============================================================
# MAIN FLIGHT TOOL
#
# Examples:
#
# flight_tool("Delhi to Chennai")
# flight_tool("Chennai to Delhi")
# flight_tool("MAA to DEL")
# flight_tool("JFK to LAX")
# ============================================================

def flight_tool(
    query: str,
    limit=20
):

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query:

        return {

            "success": False,

            "error": (
                "Flight search query "
                "cannot be empty."
            )
        }

    # --------------------------------------------------------
    # Parse route
    # --------------------------------------------------------

    origin, destination = parse_route(
        query
    )

    if not origin or not destination:

        return {

            "success": False,

            "error": (
                "Could not understand "
                "the flight route. "
                "Use format such as "
                "'Chennai to Delhi'."
            ),

            "example": (
                "Chennai to Delhi"
            )
        }

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    return search_flights(

        origin=origin,

        destination=destination,

        limit=limit
    )


# ============================================================
# LOCAL TEST
# ============================================================

# if __name__ == "__main__":

#     print(
#         "\n"
#         "========================================\n"
#         " AVIATIONSTACK FLIGHT TOOL TEST\n"
#         "========================================\n"
#     )

#     # --------------------------------------------------------
#     # Test 1
#     # --------------------------------------------------------

#     query = "Delhi to Chennai"

#     print(
#         f"Searching: {query}"
#     )

#     result = flight_tool(
#         query,
#         limit=10
#     )

#     print(
#         json.dumps(
#             result,
#             indent=2,
#             ensure_ascii=False
#         )
#     )

#     print(
#         "\n========================================"
#     )