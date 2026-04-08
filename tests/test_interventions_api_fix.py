import httpx
import json

def test_interventions_missing_student():
    """Test that interventions endpoint handles missing students gracefully."""
    api_url = "http://127.0.0.1:8006"
    
    print(f"Connecting to {api_url}/api/interventions...")
    try:
        with httpx.Client() as client:
            response = client.get(f"{api_url}/api/interventions", timeout=10.0)
            if response.status_code == 200:
                interventions = response.json()
                print(f"Received {len(interventions)} interventions.")
                for inv in interventions:
                    if "student" not in inv:
                        print("Error: 'student' key missing in intervention")
                        return False
                    if "full_name" not in inv["student"]:
                        print("Error: 'full_name' missing in student object")
                        return False
                print("Verification successful: All interventions have the required structure.")
                return True
            else:
                print(f"Error: API returned status code {response.status_code}")
                return False
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return False

if __name__ == "__main__":
    success = test_interventions_missing_student()
    if success:
        print("TEST PASSED")
    else:
        print("TEST FAILED")
        exit(1)
