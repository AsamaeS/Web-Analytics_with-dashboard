import requests
import json
import sys

# Configuration
API_URL = "http://localhost:8000/api/projects/"
PROJECT_DATA = {
    "name": "Microsoft AI Strategy",
    "domain": "Technology",
    "keywords": ["Microsoft", "Azure", "Copilot", "OpenAI", "AI"],
    "icon": "💻"
}

def create_project():
    print(f"Target URL: {API_URL}")
    print(f"Creating Project: {PROJECT_DATA['name']}...")
    
    try:
        # Send POST request
        response = requests.post(API_URL, json=PROJECT_DATA, headers={"Content-Type": "application/json"}, timeout=5)
        
        if response.status_code in [200, 201]:
            print("\n[SUCCESS] Project created successfully!")
            print("Response Data:")
            print(json.dumps(response.json(), indent=2))
            print("\n-> Now refresh your dashboard (F5) to see it in the sidebar.")
        else:
            print(f"\n[ERROR] Failed to create project. Status Code: {response.status_code}")
            print("Response Text:", response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to the server.")
        print("Make sure 'python main.py' is running in another terminal!")
    except Exception as e:
        print(f"\n[EXCEPTION] An error occurred: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
        
    create_project()
