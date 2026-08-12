from fastapi import FastAPI, HTTPException, BackgroundTasks
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError
import requests
from enum import Enum
import asyncio
import subprocess
import os
from urllib.parse import urlparse
import wandb
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
async def run(instance_id: str, bucket: str, key: str, background_tasks: BackgroundTasks):
    global health
    health = Status.RUNNING
    background_tasks.add_task(mock_run, instance_id)
    if not can_download_s3(bucket, key):
        return {
            "message":"Cannot access s3 bucket!"
        }
    return {
        "status": "scheduled",
        "message": "Running training. (mock)"
    }

async def mock_run(instance_id: str, wandb_api_key: str, bucket: str, key: str):
    # Logging setup
    wandb.login(key=os.environ.get("WANDB_API_KEY", wandb_api_key), relogin=True) # Overrides args (which are probably no good) with env var
    print("Logged in with wandb")
    # Data setup
    path = download_s3(bucket, key, "/tmp/data")
    print(f"Successfully downloaded dataset to {path}")
    # Pause execution asynchronously without blocking the server
    print("Stopping in 10 seconds. (Mock training run)")
    await asyncio.sleep(10)
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

def download_s3(bucket: str, key: str, local_dir: str = ".", signed: bool = True):
    config = Config(signature_version=UNSIGNED) if not signed else None
    s3 = boto3.client('s3', config=config)
    
    local_path = os.path.join(local_dir, os.path.basename(key))
    s3.download_file(bucket, key, local_path)
    return local_path

def can_download_s3(bucket: str, key: str, signed: bool = True) -> bool:
    if signed:
        s3 = boto3.client("s3")
    else:
        s3 = boto3.client(
            "s3",
            config=Config(signature_version=UNSIGNED),
        )

    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code in ("403", "AccessDenied"):
            print("Object exists (or is hidden), but you don't have permission.")
        elif error_code in ("404", "NoSuchKey", "NotFound"):
            print("Object does not exist.")
        else:
            print(f"S3 error: {error_code}")

        return False