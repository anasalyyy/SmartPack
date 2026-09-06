import os
import json

from dotenv import load_dotenv
from groq import Groq

from .tools import check_weather, check_destination


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()


# ==========================================
# GROQ CLIENT
# ==========================================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


MODEL = "openai/gpt-oss-120b"


# ==========================================
# AI TOOLS
# ==========================================

tools = [

    # --------------------------------------
    # DESTINATION TOOL
    # --------------------------------------

    {
        "type": "function",

        "function": {

            "name": "check_destination",

            "description": (
                "Check the characteristics of a "
                "destination such as beaches, "
                "mountains, desert and snow."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "city": {

                        "type": "string",

                        "description": (
                            "Destination city"
                        )
                    }
                },

                "required": ["city"]
            }
        }
    },


    # --------------------------------------
    # WEATHER TOOL
    # --------------------------------------

    {
        "type": "function",

        "function": {

            "name": "check_weather",

            "description": (
                "Get current weather information "
                "for a destination city."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "city": {

                        "type": "string",

                        "description": (
                            "Destination city"
                        )
                    }
                },

                "required": ["city"]
            }
        }
    }
]


# ==========================================
# MAIN AGENT
# ==========================================

def run_agent(
    destination,
    days,
    purpose,
    activities
):

    destination_result = None
    weather_result = None

    packing_list = []


    # ======================================
    # USER REQUEST
    # ======================================

    user_request = f"""
Destination: {destination}

Trip duration: {days} days

Purpose: {purpose}

Activities: {activities}
"""


    # ======================================
    # SYSTEM PROMPT
    # ======================================

    system_prompt = """
You are SmartPack, an intelligent and
professional AI travel packing assistant.

Your job is to create a practical,
personalized packing list.

You have two tools:

1. check_destination
2. check_weather


IMPORTANT PROCESS:

You MUST follow this order:

STEP 1:
Call check_destination.

STEP 2:
After receiving the destination information,
call check_weather.

STEP 3:
After receiving both results, create the
complete packing list.

STEP 4:
Do NOT call any tool again.

The goal is to keep the agent fast.


==========================================
DESTINATION VALIDATION
==========================================

Use the destination information to validate
the user's activities.

Do NOT blindly trust activities entered
by the user.

Example:

Destination: Meerut
Activity: Beach

Meerut is an inland city and does not have
a beach.

Therefore:

Do NOT recommend beach-specific items such
as swimwear, beach towel or snorkeling gear
because of that activity.

Instead, ignore the invalid activity and
continue creating a useful packing list.

If destination characteristics are unknown,
do NOT assume that the destination has a
beach, mountains, desert or snow.


==========================================
WEATHER
==========================================

Use the REAL weather returned by
check_weather.

Never invent weather information.

Consider:

- Temperature
- Humidity
- Precipitation
- Wind


==========================================
TRIP INFORMATION
==========================================

Consider:

- Number of days
- Trip purpose
- Valid activities
- Destination characteristics
- Weather


==========================================
PERSONALIZATION
==========================================

For hot weather:

Consider:

- Lightweight clothing
- Breathable clothing
- Sunglasses
- Sunscreen
- Water bottle


For cold weather:

Consider:

- Jacket
- Warm clothing
- Layers


For rainy weather:

Consider:

- Umbrella
- Rain protection
- Waterproof items


For business trips:

Consider:

- Formal clothing
- Laptop
- Charger
- Documents


For hiking:

Only when hiking is appropriate for the
destination:

- Comfortable shoes
- Outdoor essentials


For swimming:

Only when swimming is appropriate for the
destination:

- Swimwear
- Related swimming essentials


For photography:

Consider:

- Camera
- Camera charger
- Memory card


==========================================
PACKING LIST
==========================================

Create between 5 and 10 useful items.

Do NOT create unnecessary items.

Do NOT create duplicate items.

Do NOT include items only because you want
to reach 10 items.

The packing list must be practical.


==========================================
OUTPUT FORMAT
==========================================

Return ONLY valid JSON.

Use exactly this structure:

{
    "packing_list": [
        "Item 1",
        "Item 2",
        "Item 3"
    ],
    "summary": "Short professional summary with emojis."
}

IMPORTANT:

- packing_list must be a JSON array.
- Use 5 to 10 items.
- summary must contain only 2 short sentences.
- Mention the actual weather condition.
- Explain briefly why the items are suitable.
- Use 2-3 relevant emojis.
- Do not repeat the entire packing list in summary.
- Do not include markdown.
- Do not include ```json.
- Do not include any text outside the JSON.
"""


    # ======================================
    # INITIAL MESSAGES
    # ======================================

    messages = [

        {
            "role": "system",

            "content": system_prompt
        },

        {
            "role": "user",

            "content": user_request
        }

    ]


    # ======================================
    # FAST AGENT LOOP
    # ======================================

    for _ in range(4):

        response = client.chat.completions.create(

            model=MODEL,

            messages=messages,

            tools=tools,

            tool_choice="auto",

            temperature=0.2

        )


        message = response.choices[0].message


        # ==================================
        # AI FINISHED
        # ==================================

        if not message.tool_calls:

            raw_answer = message.content or ""


            # --------------------------------
            # CLEAN JSON
            # --------------------------------

            raw_answer = raw_answer.strip()


            if raw_answer.startswith("```"):

                raw_answer = (
                    raw_answer
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )


            # --------------------------------
            # PARSE JSON
            # --------------------------------

            try:

                data = json.loads(raw_answer)

                packing_list = data.get(
                    "packing_list",
                    []
                )

                summary = data.get(
                    "summary",
                    ""
                )


            except json.JSONDecodeError:

                # Fallback if AI returns invalid JSON

                packing_list = []

                summary = raw_answer


            # --------------------------------
            # CLEAN PACKING LIST
            # --------------------------------

            cleaned_list = []

            for item in packing_list:

                if not isinstance(item, str):

                    continue

                item = item.strip()

                if not item:

                    continue

                if item.lower() not in [
                    x.lower()
                    for x in cleaned_list
                ]:

                    cleaned_list.append(item)


            # --------------------------------
            # LIMIT ITEMS
            # --------------------------------

            packing_list = cleaned_list[:10]


            # --------------------------------
            # FALLBACK SUMMARY
            # --------------------------------

            if not summary:

                summary = (
                    "🎒 Your personalized packing "
                    "list is ready."
                )


            return {

                "weather": weather_result,

                "destination": destination_result,

                "packing_list": packing_list,

                "answer": summary

            }


        # ==================================
        # ADD AI MESSAGE
        # ==================================

        messages.append(message)


        # ==================================
        # EXECUTE TOOL CALLS
        # ==================================

        for tool_call in message.tool_calls:

            function_name = (
                tool_call.function.name
            )


            # --------------------------------
            # PARSE ARGUMENTS
            # --------------------------------

            try:

                arguments = json.loads(
                    tool_call.function.arguments
                )

            except json.JSONDecodeError:

                result = {
                    "error": "Invalid tool arguments."
                }

                messages.append({

                    "role": "tool",

                    "tool_call_id": tool_call.id,

                    "name": function_name,

                    "content": json.dumps(result)

                })

                continue


            print(
                f"\nTool called: {function_name}"
            )

            print(
                f"Arguments: {arguments}"
            )


            # =================================
            # DESTINATION
            # =================================

            if function_name == "check_destination":

                city = arguments.get(
                    "city",
                    destination
                )


                if destination_result is None:

                    destination_result = (
                        check_destination(city)
                    )


                result = destination_result


                print("\n📍 DESTINATION")

                print(
                    f"City: "
                    f"{result.get('city')}"
                )

                print(
                    f"Type: "
                    f"{result.get('type')}"
                )

                print(
                    f"Beach: "
                    f"{result.get('beach')}"
                )

                print(
                    f"Mountains: "
                    f"{result.get('mountains')}"
                )

                print(
                    f"Desert: "
                    f"{result.get('desert')}"
                )

                print(
                    f"Snow: "
                    f"{result.get('snow')}"
                )


            # =================================
            # WEATHER
            # =================================

            elif function_name == "check_weather":

                city = arguments.get(
                    "city",
                    destination
                )


                if weather_result is None:

                    weather_result = (
                        check_weather(city)
                    )


                result = weather_result


                if "error" not in result:

                    print("\n🌤️ WEATHER")

                    print(
                        f"City: "
                        f"{result['city']}"
                    )

                    print(
                        f"Temperature: "
                        f"{result['temperature']} °C"
                    )

                    print(
                        f"Humidity: "
                        f"{result['humidity']}%"
                    )

                    print(
                        f"Precipitation: "
                        f"{result['precipitation']} mm"
                    )

                    print(
                        f"Wind speed: "
                        f"{result['wind_speed']} km/h"
                    )


            # =================================
            # UNKNOWN TOOL
            # =================================

            else:

                result = {
                    "error": "Unknown tool."
                }


            # =================================
            # SEND RESULT BACK TO AI
            # =================================

            messages.append({

                "role": "tool",

                "tool_call_id": tool_call.id,

                "name": function_name,

                "content": json.dumps(result)

            })


    # ======================================
    # FALLBACK
    # ======================================

    return {

        "weather": weather_result,

        "destination": destination_result,

        "packing_list": packing_list,

        "answer": (
            "🎒 The packing list could not "
            "be generated completely."
        )

    }


# ==========================================
# DIRECT TESTING
# ==========================================

if __name__ == "__main__":

    destination = input(
        "Enter destination: "
    )

    days = input(
        "Enter number of days: "
    )

    purpose = input(
        "Enter purpose (Vacation/Business/etc.): "
    )

    activities = input(
        "Enter activities: "
    )


    result = run_agent(

        destination,

        days,

        purpose,

        activities

    )


    print("\n")

    print("=" * 50)

    print("SMARTPACK RESULT")

    print("=" * 50)


    # ======================================
    # DESTINATION
    # ======================================

    if result["destination"]:

        destination_data = result["destination"]

        print("\n📍 DESTINATION")

        print(
            f"City: "
            f"{destination_data.get('city')}"
        )

        print(
            f"Type: "
            f"{destination_data.get('type')}"
        )


    # ======================================
    # WEATHER
    # ======================================

    if result["weather"]:

        weather = result["weather"]

        if "error" not in weather:

            print("\n🌤️ WEATHER")

            print(
                f"City: "
                f"{weather['city']}"
            )

            print(
                f"Temperature: "
                f"{weather['temperature']} °C"
            )

            print(
                f"Humidity: "
                f"{weather['humidity']}%"
            )

            print(
                f"Precipitation: "
                f"{weather['precipitation']} mm"
            )

            print(
                f"Wind speed: "
                f"{weather['wind_speed']} km/h"
            )


    # ======================================
    # PACKING LIST
    # ======================================

    print("\n🎒 PACKING LIST")

    for number, item in enumerate(

        result["packing_list"],

        start=1

    ):

        print(
            f"{number}. {item}"
        )


    # ======================================
    # AI SUMMARY
    # ======================================

    print("\n🤖 AI SUMMARY")

    print(
        result["answer"]
    )


    print(
        "\n" + "=" * 50
    )