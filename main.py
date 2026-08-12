from fastapi import FastAPI, HTTPException, BackgroundTasks
import boto3
import requests
from enum import Enum
import asyncio
import subprocess

app = FastAPI()

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
async def run(background_tasks: BackgroundTasks):
    health = Status.RUNNING
    background_tasks.add_task(mock_run)
    return {
        "status": "scheduled",
        "message": "Instance will stop in 50 seconds."
    }

async def mock_run():
    # Pause execution asynchronously without blocking the server
    await asyncio.sleep(50)
    # Trigger the OS shutdown after the delay
    subprocess.run(["sudo", "shutdown", "-h", "now"])

@app.post("/stop")
async def stop_ec2_instance(background_tasks: BackgroundTasks):
    subprocess.run(["sudo", "shutdown", "-h", "now"])
