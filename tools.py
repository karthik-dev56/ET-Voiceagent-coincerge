from livekit.agents import RunContext, function_tool
import requests
import logging

@function_tool
async def submit_user_profile(
    context: RunContext,
    financial_goal: str,
    income_range: str,
    risk_appetite: str,
    investment_experience: str,
    time_horizon: str
) -> str:
    """
    Submit the user's financial profile after collecting all information through conversation.
    Call this function ONLY after you have collected ALL five fields from the user.

    Args:
        financial_goal: User's financial goal (e.g., wealth building, saving, tax planning, learning, retirement)
        income_range: User's income range (e.g., below 5L, 5-10L, 10-25L, 25-50L, above 50L)
        risk_appetite: User's risk tolerance level (low, medium, high)
        investment_experience: User's investment experience (beginner, intermediate, advanced)
        time_horizon: User's investment time horizon (short-term, medium-term, long-term)
    """
    try:
        url = "https://kumar54.app.n8n.cloud/webhook/ac348d4a-c007-401d-b899-b07767e4dc86"

        payload = {
            "financial_goal": financial_goal,
            "income_range": income_range,
            "risk_appetite": risk_appetite,
            "investment_experience": investment_experience,
            "time_horizon": time_horizon
        }

        logging.info(f"Submitting user profile to webhook: {payload}")

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        logging.info(f"Webhook response: {response.status_code}")
        return "User profile successfully submitted. You can now provide personalized recommendations."

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP error submitting profile: {e}")
        return "Profile recorded. Proceeding with recommendations."
    except Exception as e:
        logging.error(f"Error submitting user profile: {e}")
        return "Profile recorded. Proceeding with recommendations."

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, EMERGENCY_CONTACT
import time


@function_tool
async def call_emergency(context: RunContext, user_name: str, mobile_number: str) -> str:
    """use this when user wants customer support for our services or when user is facing any issue and wants to talk to customer support"""

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    message = f"""
    Hello, this is ET Customer Service.
    We have a support request from {user_name}.
    They need assistance with our financial services.
    Please call them back at {mobile_number}.
    Thank you.
    """

    response = VoiceResponse()

    response.say(message, voice='alice')

    call = client.calls.create(
            to=EMERGENCY_CONTACT,
            from_=TWILIO_FROM_NUMBER,
            twiml=str(response),
            timeout=20
        )

    client.messages.create(
        body=f"ET Customer Support Request - Name: {user_name}, Mobile: {mobile_number}",
        to=EMERGENCY_CONTACT,
        from_=TWILIO_FROM_NUMBER
    )

    return f"Thanks {user_name}! I've notified our customer service team. They will call you back at {mobile_number} within the next 30 minutes to help with your request."

