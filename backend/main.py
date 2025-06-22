from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from dotenv import load_dotenv
import os
import httpx
import uuid

load_dotenv()

app = FastAPI(title="Weather Data System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for weather data
weather_storage: Dict[str, Dict[str, Any]] = {}

class WeatherRequest(BaseModel):
    date: str
    location: str
    notes: Optional[str] = ""

class WeatherResponse(BaseModel):
    id: str

## API Key
WeatherStackAPI = os.getenv("WeatherStackAPI")

## URL
WeatherStackURL = r"http://api.weatherstack.com/current"

@app.post("/weather", response_model=WeatherResponse)
async def create_weather_request(request: WeatherRequest):
    """
    You need to implement this endpoint to handle the following:
    1. Receive form data (date, location, notes)
    2. Calls WeatherStack API for the location
    3. Stores combined data with unique ID in memory
    4. Returns the ID to frontend
    """
    params = {
        "access_key": WeatherStackAPI,
        "query": request.location
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(WeatherStackURL, params=params)
            weather_data = response.json()
            
            weather_id = str(uuid.uuid4())

            if "error" in weather_data:
                raise HTTPException(status_code = 400, detail = "WeatherStack API Error")

            combined_data = {
                "weather id": weather_id,
                "date": request.date,
                "location": request.location,
                "notes": request.notes,
                "weather_api_response": weather_data
            }

            weather_storage[weather_id] = combined_data
            return WeatherResponse(id = weather_id)
       
        except httpx.RequestError as e:
            raise HTTPException(status_code = 502, detail = f"Network Error: {str(e)}")
       
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code = e.response.status_code, detail = f"Error from WeatherStackAPI: {str(e)}")
       
        except Exception as e:
            raise HTTPException(status_code = 500, detail = "Internal Server Errors")
    
@app.get("/weather/astro/{weather_id}")
async def get_astronomy_data(weather_id: str):
    '''
    Get astronomy data through weather_storage
    '''
    if weather_id not in weather_storage:
        raise HTTPException(status_code=404, detail="Weather data not found")
    
    data = weather_storage[weather_id]
    try:
        astro = data["weather_api_response"]["current"]["astro"]
        return astro
    except Exception:
        raise HTTPException(status_code=404, detail="No data available")

@app.get("/weather/location/{weather_id}")
async def get_precise_location(weather_id: str):
    '''
    Get the location through weather_storage
    '''
    if weather_id not in weather_storage:
        raise HTTPException(status_code=404, detail="Weather data not found")
    
    data = weather_storage[weather_id]
    try:
        location = data["weather_api_response"]["location"]
        return location
    except Exception:
        raise HTTPException(status_code=404, detail="No data available")

@app.get("/weather/air-quality/{weather_id}")
async def get_air_quality_data(weather_id: str):
    '''
    Get air quality data through weather_storage
    '''
    if weather_id not in weather_storage:
        raise HTTPException(status_code=404, detail="Weather data not found")
    
    data = weather_storage[weather_id]
    try:
        air_data = data["weather_api_response"]["current"]["air_quality"]
        return air_data
    except Exception:
        raise HTTPException(status_code=404, detail="No data available")


@app.get("/weather/{weather_id}")
async def get_weather_data(weather_id: str):
    """
    Retrieve stored weather data by ID.
    This endpoint is already implemented for the assessment.
    """
    if weather_id not in weather_storage:
        raise HTTPException(status_code=404, detail="Weather data not found")
    
    return weather_storage[weather_id]



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)