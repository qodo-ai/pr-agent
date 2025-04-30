import os
import boto3
from fastapi import FastAPI
from mangum import Mangum
from starlette.middleware import Middleware
from botocore.exceptions import ClientError
from starlette_context.middleware import RawContextMiddleware

from pr_agent.config_loader import get_settings
from pr_agent.servers.github_app import router

middleware = [Middleware(RawContextMiddleware)]
app = FastAPI(middleware=middleware)
app.include_router(router)

handler = Mangum(app, lifespan="off")

def get_secret(secret_name, region_name):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return get_secret_value_response['SecretString']

# Retrieve the secret and set it as an environment variable
secret_name = get_settings().aws.secret_name
region_name = get_settings().aws.region_name

secret_value = get_secret(secret_name, region_name)
if secret_value:
    os.environ['GITHUB_PRIVATE_KEY'] = secret_value

def serverless(event, context):
    return handler(event, context)
