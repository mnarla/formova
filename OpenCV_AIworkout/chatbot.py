import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini from environment variable
API_KEY = os.environ.get("GOOGLE_API_KEY", "")

def get_chatbot_response(message):
    """Get a response from the Gemini model using direct API call"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Check if the message is about workout or diet plans
        if "workout" in message.lower() or "diet" in message.lower() or "fitness plan" in message.lower():
            formatted_message = f"{message}\n\nFormat your response as follows:\n1. Start with a brief intro\n2. List exercises/foods with:\n   - Item 1\n   - Item 2\n   - etc.\n3. Add 2-3 key tips at the end"
        else:
            formatted_message = f"{message}\n\nProvide a clear response in 2-3 sentences."
        
        data = {
            "contents": [{
                "parts":[{"text": formatted_message}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  
        
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            return {"response": result['candidates'][0]['content']['parts'][0]['text']}
        else:
            return {"response": "No response generated"}
            
    except Exception as e:
        return {"response": f"Sorry, I couldn't process your request. ({str(e)})"}

if __name__ == "__main__":
    # Example usage
    user_data = {
        "height": "5'10\"",
        "weight": "180",
        "age": "30",
        "gender": "male",
        "goal": "lose weight",
        "workout_preference": "strength training",
        "diet_preference": "balanced"
    }
    
    # Convert user data to a message
    message = f"Create a fitness plan for: {user_data}"
    response = get_chatbot_response(message)
    print("\n=== Your Personalized Fitness Plan ===")
    print(response["response"])
