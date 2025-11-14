from dotenv import load_dotenv
from vertexai import agent_engines

load_dotenv()  # May skip if you have exported environment variables.

agent_engine_id = (
    "projects/745425319636/locations/us-central1/reasoningEngines/2466578415055011840"
)
user_input = "我要拜訪客戶沃司科技，我是思想科技台北出發，客戶是在No. 655號, Bannan Rd, Zhonghe District, New Taipei City, 235"

remote_app = agent_engines.get(agent_engine_id)
print(f"Remote App: {remote_app.display_name}")

remote_session = remote_app.create_session(user_id="sean")
print(remote_session)

for event in remote_app.stream_query(
    user_id="sean",
    session_id=remote_session["id"],
    message=user_input,
):
    print(f"Event: {event}")
