import boto3
from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

# Create a client for the API Gateway service
client = boto3.client('apigateway')

class UsagePlan(BaseModel):
    Usage_Plan_ID: str
    Name: str
    Description: Optional[str] = "No description"
    Quota: Optional[dict] = "No quota"
    Throttle: Optional[dict] = "No throttle"

class APIKey(BaseModel):
    API_Key_ID: str
    Name: str
    Usage_Plans: List[UsagePlan]

@app.get("/api-keys", response_model=List[APIKey])
def get_api_keys():
    # Retrieve the list of API keys
    response = client.get_api_keys()

    api_keys_with_usage_plans = []

    # Iterate over each API key
    for api_key in response['items']:
        api_key_info = {
            "API_Key_ID": api_key['id'],
            "Name": api_key['name'],
            "Usage_Plans": []
        }
        
        # Retrieve the usage plans associated with the API key
        usage_plans_response = client.get_usage_plans(keyId=api_key['id'])
        
        for usage_plan in usage_plans_response['items']:
            usage_plan_info = {
                "Usage_Plan_ID": usage_plan['id'],
                "Name": usage_plan['name'],
                "Description": usage_plan.get('description', 'No description'),
                "Quota": usage_plan.get('quota', {}),
                "Throttle": usage_plan.get('throttle', {})
            }
            api_key_info["Usage_Plans"].append(usage_plan_info)
        
        api_keys_with_usage_plans.append(api_key_info)
    
    return api_keys_with_usage_plans

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)