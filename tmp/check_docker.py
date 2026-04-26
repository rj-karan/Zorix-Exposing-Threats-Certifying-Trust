import docker
import traceback

try:
    client = docker.from_env()
    print("Ping:", client.ping())
except Exception as e:
    print("Error during docker.from_env():")
    traceback.print_exc()
