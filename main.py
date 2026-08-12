from fastapi import FastAPI, HTTPException, BackgroundTasks
import boto3
import requests
from enum import Enum
import asyncio
import subprocess
REGION = "us-east-2"
INSTANCE_TABLE_NAME = "TEST_DEV_INSTANCES"
app = FastAPI()
dynamodb = boto3.resource("dynamodb", region_name=REGION)
instances_table = dynamodb.Table(INSTANCE_TABLE_NAME)
class Status(Enum):
    RUNNING = 1
    READY = 2
    DONE = 3

health = Status.READY

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on EC2 t3.medium!"}

@app.get("/health")
def get_health():
    return {"message": f"{health.name}"}

@app.post("/run")
async def run(instance_id: str, background_tasks: BackgroundTasks):
    global health
    health = Status.RUNNING
    background_tasks.add_task(mock_run, instance_id)
    return {
        "status": "scheduled",
        "message": "Instance will stop in 50 seconds."
    }

async def mock_run(instance_id: str):
    # Pause execution asynchronously without blocking the server
    await asyncio.sleep(50)
    # Trigger the OS shutdown after the delay
    stop_this_instance(instance_id)

@app.post("/stop")
async def stop_ec2_instance(instance_id: str, background_tasks: BackgroundTasks):
    stop_this_instance(instance_id)

def stop_this_instance(instance_id: str):
    print(f"Stopping instance: {instance_id}")
    instances_table.update_item(
        Key={
            "instance_id": instance_id
        },
        UpdateExpression="SET #status = :available",
        ExpressionAttributeNames={
            "#status": "status"
        },
        ExpressionAttributeValues={
            ":available": "available"
        }
    )
    subprocess.run(["sudo", "shutdown", "-h", "now"])
