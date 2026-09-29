# ruff: noqa
import json
import os
import requests
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types
from google.genai import Client as GenaiClient
from google.cloud import firestore
from google.cloud import storage

from .a2ui_utils import a2ui_callback

PROJECT_ID = "qwiklabs-gcp-04-15689d1f930e"
LOCATION = "us-east1"
BUCKET_NAME = "wanderlust-planner-qwiklabs-gcp-04-15689d1f930e"
MODEL = "gemini-3.6-flash"

# Firestore database instance
db = firestore.Client(project=PROJECT_ID)

# 1. Tool: List destinations from Firestore
def list_destinations() -> str:
    """Lists available travel destinations stored in the catalog.

    Returns:
        JSON string representing the list of destinations with key details.
    """
    try:
        docs = db.collection("destinations").stream()
        results = [d.to_dict() for d in docs]
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})

# 2. Tool: Get destination details from Firestore
def get_destination_details(destination_id: str) -> str:
    """Gets complete details, season, budget, and attractions for a destination.

    Args:
        destination_id: The ID of the destination (e.g. 'kyoto-japan', 'rome-italy', 'reykjavik-iceland', 'banff-canada').

    Returns:
        JSON string with destination info.
    """
    try:
        doc = db.collection("destinations").document(destination_id).get()
        if doc.exists:
            return json.dumps(doc.to_dict())
        return json.dumps({"error": f"Destination '{destination_id}' not found."})
    except Exception as e:
        return json.dumps({"error": str(e)})

# 3. Tool: Live weather lookup using Open-Meteo free API
def get_live_destination_weather(latitude: float, longitude: float) -> str:
    """Fetches real-time weather using Open-Meteo API for given coordinates.

    Args:
        latitude: Latitude of the destination (e.g. 35.0116 for Kyoto, 41.9028 for Rome).
        longitude: Longitude of the destination (e.g. 135.7681 for Kyoto, 12.4964 for Rome).

    Returns:
        JSON string with current temperature in Celsius, windspeed, and weather condition.
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("current_weather", {})
        return json.dumps({
            "temperature_celsius": data.get("temperature"),
            "windspeed_kmh": data.get("windspeed"),
            "weathercode": data.get("weathercode")
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

# 4. Tool: Generate scenic travel image with gemini-3.1-flash-lite-image and save to GCS
def generate_destination_image(prompt: str, filename: str) -> str:
    """Generates a scenic postcard or destination hero image using gemini-3.1-flash-lite-image in the global region.
    Uploads the image to Google Cloud Storage and returns the public HTTPS URL.

    Args:
        prompt: A descriptive visual prompt for the destination or landmark.
        filename: A short filename like 'kyoto_temple.png' or 'banff_lake.png'.

    Returns:
        A public HTTPS URL to view the generated image.
    """
    try:
        genai_client = GenaiClient(project=PROJECT_ID, location="global")
        response = genai_client.models.generate_images(
            model="gemini-3.1-flash-lite-image",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/png",
                aspect_ratio="1:1"
            )
        )
        if not response.generated_images:
            return json.dumps({"error": "No image generated."})

        image_bytes = response.generated_images[0].image.image_bytes
        
        # Upload to Cloud Storage
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/png")
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return json.dumps({"public_url": public_url, "status": "success"})
    except Exception as e:
        return json.dumps({"error": str(e)})

# WRITE Memory callback
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None

prompt_path = os.path.join(os.path.dirname(__file__), "instruction_prompt.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    instruction = f.read()

root_agent = Agent(
    name="wanderlust_planner",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_destinations,
        get_destination_details,
        get_live_destination_weather,
        generate_destination_image,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

from google.adk.apps import App
app = App(root_agent=root_agent, name="wanderlust_planner")

