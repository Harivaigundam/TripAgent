/* =========================================================
   CONFIGURATION
========================================================= */

const API_URL = "/api/travel";


/* =========================================================
   DOM ELEMENTS
========================================================= */

const travelForm = document.getElementById("travelForm");

const travelQuery = document.getElementById("travelQuery");

const charCount = document.getElementById("charCount");

const clearBtn = document.getElementById("clearBtn");

const planBtn = document.getElementById("planBtn");

const planBtnText = document.getElementById("planBtnText");

const agentSection = document.getElementById("agentSection");

const resultsSection = document.getElementById("resultsSection");

const workflowStatus = document.getElementById("workflowStatus");

const finalResponse = document.getElementById("finalResponse");

const flightResult = document.getElementById("flightResult");

const hotelResult = document.getElementById("hotelResult");

const itineraryResult = document.getElementById("itineraryResult");

const errorBox = document.getElementById("errorBox");

const errorMessage = document.getElementById("errorMessage");

const closeError = document.getElementById("closeError");

const newTripBtn = document.getElementById("newTripBtn");

const copyBtn = document.getElementById("copyBtn");

const quickPrompts =
    document.querySelectorAll(".quick-prompt");


/* =========================================================
   CHARACTER COUNTER
========================================================= */

travelQuery.addEventListener("input", () => {

    const length = travelQuery.value.length;

    charCount.textContent =
        `${length} / 2000`;

});


/* =========================================================
   QUICK PROMPTS
========================================================= */

quickPrompts.forEach(button => {

    button.addEventListener("click", () => {

        const query =
            button.dataset.query;

        travelQuery.value = query;

        charCount.textContent =
            `${query.length} / 2000`;

        travelQuery.focus();

    });

});


/* =========================================================
   CLEAR BUTTON
========================================================= */

clearBtn.addEventListener("click", () => {

    travelQuery.value = "";

    charCount.textContent = "0 / 2000";

    travelQuery.focus();

});


/* =========================================================
   CLOSE ERROR
========================================================= */

closeError.addEventListener("click", () => {

    hideError();

});


/* =========================================================
   FORM SUBMIT
========================================================= */

travelForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const query =
        travelQuery.value.trim();


    /* ---------------------------------------------
       Client-side validation
    --------------------------------------------- */

    if (!query) {

        showError(
            "Please describe your travel requirements."
        );

        travelQuery.focus();

        return;
    }


    if (query.length < 10) {

        showError(
            "Please provide a little more information about your trip."
        );

        travelQuery.focus();

        return;
    }


    hideError();

    startPlanning();


    try {

        /*
         * FastAPI expected request:
         *
         * POST /api/travel
         *
         * {
         *     "user_query": "..."
         * }
         */

        const response = await fetch("/api/travel", {
                    method: "POST",

                    headers: {
                            "Content-Type": "application/json"
                        },

                    body: JSON.stringify({
                        user_query: query
                    })
            });


        /* ---------------------------------------------
           HTTP error handling
        --------------------------------------------- */

        if (!response.ok) {

            let errorText =
                `Server returned HTTP ${response.status}.`;

            try {

                const errorData =
                    await response.json();

                errorText =
                    extractErrorMessage(errorData)
                    || errorText;

            } catch {
                // Response wasn't JSON.
            }

            throw new Error(errorText);
        }


        /* ---------------------------------------------
           Parse API response
        --------------------------------------------- */

        const data =
            await response.json();


        /*
         * API response successfully received.
         */

        finishPlanning();

        renderResults(data);


    } catch (error) {

        console.error(
            "Travel API Error:",
            error
        );

        stopPlanningWithError(
            error.message ||
            "Unable to connect to the travel planning service."
        );

    }

});


/* =========================================================
   START PLANNING
========================================================= */

function startPlanning() {

    /*
     * Show agent workflow.
     */

    agentSection.classList.remove("hidden");

    /*
     * Hide previous results.
     */

    resultsSection.classList.add("hidden");

    /*
     * Disable submit button.
     */

    planBtn.disabled = true;

    planBtnText.textContent =
        "Planning your trip...";


    /*
     * Reset agent cards.
     */

    resetAgentCards();


    /*
     * Scroll to workflow.
     */

    setTimeout(() => {

        agentSection.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

    }, 100);


    /*
     * Because the API response is returned only after
     * the backend graph completes, the frontend cannot
     * know the exact node execution status unless the
     * backend provides streaming/websocket updates.
     *
     * Therefore we show a visual workflow animation.
     */

    animateAgents();

}


/* =========================================================
   AGENT ANIMATION
========================================================= */

function animateAgents() {

    const agents = [
        "flightAgent",
        "hotelAgent",
        "itineraryAgent",
        "finalAgent"
    ];

    agents.forEach((agentId, index) => {

        setTimeout(() => {

            if (
                !agentSection.classList.contains("hidden")
            ) {

                setAgentActive(agentId);

            }

        }, index * 1100);

    });

}


/* =========================================================
   SET ACTIVE AGENT
========================================================= */

function setAgentActive(agentId) {

    const agent =
        document.getElementById(agentId);

    if (!agent) {
        return;
    }


    /*
     * Complete previous agent.
     */

    const agents = [
        "flightAgent",
        "hotelAgent",
        "itineraryAgent",
        "finalAgent"
    ];

    const currentIndex =
        agents.indexOf(agentId);


    for (
        let i = 0;
        i < currentIndex;
        i++
    ) {

        const previous =
            document.getElementById(agents[i]);

        previous.classList.remove("active");

        previous.classList.add("completed");

    }


    agent.classList.add("active");

}


/* =========================================================
   COMPLETE PLANNING
========================================================= */

function finishPlanning() {

    const agents = [
        "flightAgent",
        "hotelAgent",
        "itineraryAgent",
        "finalAgent"
    ];


    agents.forEach(agentId => {

        const agent =
            document.getElementById(agentId);

        if (!agent) {
            return;
        }

        agent.classList.remove("active");

        agent.classList.add("completed");

    });


    workflowStatus.textContent =
        "Completed";

    workflowStatus.style.color =
        "var(--green)";


    planBtn.disabled = false;

    planBtnText.textContent =
        "Plan My Trip";

}


/* =========================================================
   STOP PLANNING WITH ERROR
========================================================= */

function stopPlanningWithError(message) {

    planBtn.disabled = false;

    planBtnText.textContent =
        "Plan My Trip";

    workflowStatus.textContent =
        "Failed";

    workflowStatus.style.color =
        "var(--red)";

    showError(message);

}


/* =========================================================
   RENDER RESULTS
========================================================= */

function renderResults(data) {

    /*
     * Support multiple possible FastAPI response
     * structures.
     *
     * Preferred:
     *
     * {
     *   "final_response": "...",
     *   "flight_result": "...",
     *   "hotel_result": "...",
     *   "itinerary": "...",
     *   "llm_calls": 4
     * }
     */


    const finalText =
        getValue(
            data,
            [
                "final_response",
                "finalResponse",
                "response",
                "answer"
            ]
        );


    const flights =
        getValue(
            data,
            [
                "flight_result",
                "flightResult",
                "flights",
                "flight"
            ]
        );


    const hotels =
        getValue(
            data,
            [
                "hotel_result",
                "hotelResult",
                "hotels",
                "hotel"
            ]
        );


    const itinerary =
        getValue(
            data,
            [
                "itinerary",
                "Itinerary",
                "travel_itinerary"
            ]
        );


    /*
     * Render each section.
     */

    finalResponse.textContent =
        formatValue(
            finalText,
            "The AI travel plan was generated, but no final response was returned."
        );


    flightResult.textContent =
        formatValue(
            flights,
            "Live flight information was not available."
        );


    hotelResult.textContent =
        formatValue(
            hotels,
            "Hotel information was not available."
        );


    itineraryResult.textContent =
        formatValue(
            itinerary,
            "An itinerary was not returned."
        );


    /*
     * Show results.
     */

    resultsSection.classList.remove(
        "hidden"
    );


    /*
     * Scroll to results.
     */

    setTimeout(() => {

        resultsSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 200);

}


/* =========================================================
   VALUE EXTRACTION
========================================================= */

function getValue(object, keys) {

    if (!object || typeof object !== "object") {

        return null;
    }


    for (const key of keys) {

        if (
            Object.prototype.hasOwnProperty.call(
                object,
                key
            )
        ) {

            const value =
                object[key];

            if (
                value !== null &&
                value !== undefined &&
                value !== ""
            ) {

                return value;

            }

        }

    }


    return null;

}


/* =========================================================
   FORMAT API VALUES
========================================================= */

function formatValue(value, fallback) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return fallback;

    }


    /*
     * If FastAPI returns an array.
     */

    if (Array.isArray(value)) {

        return value
            .map(item => {

                if (
                    typeof item === "object"
                ) {

                    return JSON.stringify(
                        item,
                        null,
                        2
                    );

                }

                return String(item);

            })
            .join("\n\n");

    }


    /*
     * If FastAPI returns an object.
     */

    if (
        typeof value === "object"
    ) {

        return JSON.stringify(
            value,
            null,
            2
        );

    }


    return String(value);

}


/* =========================================================
   ERROR MESSAGE EXTRACTION
========================================================= */

function extractErrorMessage(data) {

    if (!data) {
        return null;
    }


    if (typeof data === "string") {
        return data;
    }


    if (data.detail) {

        if (typeof data.detail === "string") {

            return data.detail;

        }

        return JSON.stringify(
            data.detail
        );

    }


    if (data.message) {

        return data.message;

    }


    if (data.error) {

        if (typeof data.error === "string") {

            return data.error;

        }

        return JSON.stringify(
            data.error
        );

    }


    return null;

}


/* =========================================================
   SHOW ERROR
========================================================= */

function showError(message) {

    errorMessage.textContent =
        message;

    errorBox.classList.remove(
        "hidden"
    );

}


/* =========================================================
   HIDE ERROR
========================================================= */

function hideError() {

    errorBox.classList.add(
        "hidden"
    );

}


/* =========================================================
   RESET AGENTS
========================================================= */

function resetAgentCards() {

    const agents = [
        "flightAgent",
        "hotelAgent",
        "itineraryAgent",
        "finalAgent"
    ];


    agents.forEach(agentId => {

        const agent =
            document.getElementById(agentId);

        if (!agent) {
            return;
        }

        agent.classList.remove(
            "active",
            "completed"
        );

    });


    workflowStatus.textContent =
        "Processing";

    workflowStatus.style.color =
        "var(--orange)";

}


/* =========================================================
   NEW TRIP
========================================================= */

newTripBtn.addEventListener("click", () => {

    resultsSection.classList.add(
        "hidden"
    );

    agentSection.classList.add(
        "hidden"
    );

    travelQuery.value = "";

    charCount.textContent =
        "0 / 2000";

    hideError();

    resetAgentCards();

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

    setTimeout(() => {

        travelQuery.focus();

    }, 500);

});


/* =========================================================
   COPY FINAL RESPONSE
========================================================= */

copyBtn.addEventListener("click", async () => {

    const text =
        finalResponse.textContent.trim();


    if (!text) {
        return;
    }


    try {

        await navigator.clipboard.writeText(
            text
        );

        copyBtn.textContent =
            "✓ Copied";

        setTimeout(() => {

            copyBtn.textContent =
                "⧉ Copy";

        }, 1800);

    } catch (error) {

        console.error(
            "Copy failed:",
            error
        );

        showError(
            "Unable to copy the travel plan."
        );

    }

});