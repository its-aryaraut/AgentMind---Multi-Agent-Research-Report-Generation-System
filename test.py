import time
import sys
import requests

BASE_URL = "http://localhost:8000"

def run_research(topic: str):
    print(f"\n🚀 Starting Multi-Agent Research on: '{topic}'")
    
    # 1. Start the workflow
    try:
        response = requests.post(f"{BASE_URL}/research", json={"topic": topic})
        response.raise_for_status()
        data = response.json()
        thread_id = data["thread_id"]
        print(f"✅ Workflow started. Thread ID: {thread_id}\n")
    except Exception as e:
        print(f"❌ Failed to start research: {e}")
        return

    # Give the FastAPI background task a moment to initialize the graph state
    time.sleep(2) 

    # 2. Poll for status
    while True:
        try:
            status_res = requests.get(f"{BASE_URL}/research/{thread_id}/status")
            
            # Handle the race condition where the thread isn't saved to memory yet
            if status_res.status_code == 404:
                sys.stdout.write("⏳ Initializing state...")
                sys.stdout.flush()
                time.sleep(2)
                continue

            status_res.raise_for_status()
            status_data = status_res.json()
            
            current_status = status_data["status"]
            
            if current_status == "running":
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(3) 
                
            elif current_status == "awaiting_approval":
                print(f"\n\n🛑 HUMAN IN THE LOOP PAUSE")
                print(f"Subtopics planned: {status_data.get('research_plan')}")
                print(f"Verified facts extracted: {status_data.get('verified_facts_count')}")
                
                user_input = input("Do you approve this research to move to the Writer Agent? (y/n): ").strip().lower()
                action = "approve" if user_input == 'y' else "reject"
                
                requests.post(f"{BASE_URL}/research/{thread_id}/approve", json={"action": action})
                print(f"✅ Action '{action}' submitted. Resuming workflow...\n")
                
            elif current_status == "completed":
                print(f"\n🎉 Research Complete!")
                print(f"📄 Report saved to: {status_data.get('report_pdf')}")
                break
                
            else:
                print(f"\n⚠️ Unknown status: {current_status}")
                break
                
        except Exception as e:
            print(f"\n❌ Error checking status: {e}")
            break

if __name__ == "__main__":
    target_topic = "The economic impact of Agentic AI in healthcare"
    run_research(target_topic)