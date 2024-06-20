import functions_framework
import google.auth
import google.auth.transport.requests
import requests

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def hello_gcs(cloud_event):
    data = cloud_event.data
    event_id = cloud_event["id"]
    event_type = cloud_event["type"]
    bucket = data["bucket"]
    name = data["name"]
    metageneration = data["metageneration"]
    timeCreated = data["timeCreated"]
    updated = data["updated"]

    gcs_path = f'gs://{bucket}/{name}'

    creds, project = google.auth.default()

    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "x-goog-user-project": "", # project id
        "Content-Type": "application/json; charset=utf-8"
    }

    # Replace with your project ID and location
    project_id = "" # project id
    location = "asia-southeast2"

    # Replace with your template path and job name
    template_path = "" # gcs template path
    job_name = "ETL-Demo-Dataset-1"

    # Build the request URL
    url = f"https://dataflow.googleapis.com/v1b3/projects/{project_id}/locations/{location}/templates:launch?gcsPath={template_path}"

    # Prepare the request body
    body = {
        "jobName": job_name,
        "environment": {
            "bypassTempDirValidation": False,
            "tempLocation": "", # temp location
            "ipConfiguration": "WORKER_IP_UNSPECIFIED",
            "enableStreamingEngine": False,
            "additionalExperiments": [],
            "additionalUserLabels": {}
        },
        "parameters": {
            "input": gcs_path
        }
    }

    # Send the request
    response = requests.post(url, json=body, headers=headers)

    # Check for errors
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
    else:
        print("Job launched successfully!")

    print(gcs_path)
