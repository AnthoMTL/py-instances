from google.cloud import billing_v1
from google.cloud import resourcemanager_v3
from google.cloud.resourcemanager_v3 import types
from google.cloud import compute_v1
from google.cloud import service_usage_v1
from google.api_core import operation
from google.cloud import storage
#from google.cloud import iam_admin_v1
import uuid
import os
import random
import time
import streamlit as st


def upload_files_to_bucket(project_id, uploaded_files, bucket_name):
    storage_client = storage.Client(project=project_id)
    #bucket_name = project_id  # Assuming the bucket name is the same as the project ID
    bucket = storage_client.bucket(bucket_name)

    for uploaded_file in uploaded_files:
        try:
            file_name = uploaded_file.name
            blob = bucket.blob(file_name)
            with st.spinner("Uploading...", show_time=True):
                blob.upload_from_file(uploaded_file)
            st.success(f"File '{file_name}' uploaded.", icon="✅")
        except Exception as e:
            st.error(f"Error uploading file '{file_name}': {e}")
            return

def create_regional_standard_bucket(project_id, region):
    """
    Creates a regional standard bucket with uniform access control.

    Args:
        project_id: The ID of the project.
        region: The region in which to create the bucket.
    """
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    bucket.location = region
    bucket.storage_class = "STANDARD"
    bucket.iam_configuration.uniform_bucket_level_access_enabled = True

    try:
        bucket = storage_client.create_bucket(bucket)
        print(f"Bucket {bucket.name} created in {bucket.location} with storage class {bucket.storage_class} and uniform access control.")
        return bucket
    except Exception as e:
        raise ValueError(f"Error creating bucket: {e}")

if __name__ == "__main__":
    project_id = "test-metal-358914"
    bucket_name = "upload-test-atkins-y123"
    region = "us-central1"

    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True)
    if st.button("Upload", type="primary"):
        if uploaded_files is not None:
            upload_files_to_bucket(project_id, uploaded_files, bucket_name)
