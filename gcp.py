from google.cloud import billing_v1
from google.cloud import resourcemanager_v3
from google.cloud.resourcemanager_v3 import types
import uuid
import os
from google.cloud import compute_v1
from google.cloud import serviceusage_v1
from google.api_core import operation
import time

# Static variable for the billing account ID
BILLING_ACCOUNT_ID = "billingAccounts/015F68-FEF42E-E10820"  # Replace with your actual billing account ID - new format
TARGET_FOLDER_PATH = ["North America", "NA-LAB"]  # Define the path to the target folder.
ORGANIZATION_ID = "organizations/690423753921"  # Replace with your actual organization id


def find_folder_id_recursive(folder_client, parent, folder_path):
    """
    Recursively finds the folder ID based on the folder path.

    Args:
        folder_client: The resourcemanager_v3.FoldersClient.
        parent: The parent resource (organization or folder) to start the search.
        folder_path: A list of folder names representing the path (e.g., ["North America", "NA-LAB"]).

    Returns:
        The folder ID (full resource name) if found, otherwise None.
    """
    if not folder_path:
        return parent  # return the root folder if the path is empty.

    current_folder_name = folder_path[0]
    list_request = resourcemanager_v3.ListFoldersRequest(
        parent=parent, page_size=100, show_deleted=False
    )
    print(f"Searching for folder '{current_folder_name}' under parent '{parent}'")  # Debugging
    for folder in folder_client.list_folders(request=list_request):
        print(f"  Found folder: {folder.display_name} (name: {folder.name})")  # Debugging
        if folder.display_name == current_folder_name:
            # Found the current folder in the path.
            remaining_path = folder_path[1:]  # Get the rest of the path.
            if not remaining_path:
                print(f"    Found target folder: {folder.name}")  # Debugging
                return folder.name  # This was the last folder in the path.
            else:
                # Recursively search in the child folder.
                return find_folder_id_recursive(folder_client, folder.name, remaining_path)
    print(f"Folder '{current_folder_name}' not found under '{parent}'")  # Debugging
    return None  # Folder not found at this level.


def create_project_in_folder(project_id):
    """Creates a Google Cloud project inside a specific folder and attaches a billing account."""

    project_client = resourcemanager_v3.ProjectsClient()
    billing_client = billing_v1.CloudBillingClient()
    folder_client = resourcemanager_v3.FoldersClient()

    # Start the search from the organization
    print(f"Starting project creation for project ID: {project_id}")  # Debugging
    print(f"Using organization ID: {ORGANIZATION_ID}")  # Debugging
    folder_full_id = find_folder_id_recursive(folder_client, ORGANIZATION_ID, TARGET_FOLDER_PATH)

    if folder_full_id is None:
        raise ValueError(f"Folder path '{TARGET_FOLDER_PATH}' not found.")
    print(f"Found folder ID: {folder_full_id}")  # Debugging

    project = resourcemanager_v3.Project()
    project.project_id = project_id
    project.display_name = project_id
    #project.parent = types.Folder(name=folder_full_id) # old code
    project.parent = folder_full_id # new code
    print(f"Project parent set to : {project.parent}")
    operation = project_client.create_project(project=project)

    try:
        response = operation.result()
    except Exception as e:
        raise ValueError(f"An error occurred during the project creation: {e}")
    print(f"Project created successfully : {response.project_id}")  # Debugging

    project_name = f"projects/{project_id}"

    # Set Billing account
    try:
        print(f"Attaching billing account: {BILLING_ACCOUNT_ID} to project : {project_name}")  # Debugging
        billing_client.update_project_billing_info(
            name=project_name, project_billing_info={"billing_account_name": BILLING_ACCOUNT_ID}
        )
        print(f"Billing account attached successfully to {project_name}")  # Debugging
    except Exception as e:
        raise ValueError(f"An error occurred when attaching the billing account: {e}")

    return response


def generate_unique_project_id():
    """Generates a unique project ID."""
    return f"atkins-project-{uuid.uuid4().hex[:4]}"


# Example Usage (Optional):
#if __name__ == "__main__":
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "B:\Code\Atkins\credentials.json" # Uncomment if you want to use the json file
#    new_project_id = generate_unique_project_id()


def enable_compute_engine_api(project_id):
    """Enables the Compute Engine API for the specified project."""

    service_client = serviceusage_v1.ServiceUsageClient()
    service_name = f"projects/{project_id}/services/compute.googleapis.com"

    try:
        # Check if the service is already enabled
        get_request = serviceusage_v1.GetServiceRequest(name=service_name)
        service = service_client.get_service(request=get_request)
        if service.state == serviceusage_v1.Service.State.ENABLED:
            print(f"Compute Engine API is already enabled for project: {project_id}")
            return

        # Enable the service
        enable_request = serviceusage_v1.EnableServiceRequest(name=service_name)
        operation = service_client.enable_service(request=enable_request)

        print(f"Enabling Compute Engine API for project: {project_id}...")
        response = operation.result()  # Wait for the operation to complete
        print(f"Compute Engine API enabled successfully for project: {project_id}")
        return response

    except Exception as e:
        raise ValueError(f"Error enabling Compute Engine API: {e}")


def create_custom_vpc_with_subnet(project_id, region="us-central1"):
    """
    Creates a custom VPC network with a subnet in the specified region.

    Args:
        project_id: The ID of the project.
        region: The region in which to create the subnet (default: us-central1).
    """
    network_client = compute_v1.NetworksClient()
    subnet_client = compute_v1.SubnetworksClient()

    network_name = "atkins-custom-vpc"
    subnet_name = "atkins-subnet"
    ip_range = "172.18.100.0/24"

    # Check if the network already exists
    try:
        network_client.get(
            project=project_id, network=network_name
        )
        print(f"VPC network '{network_name}' already exists in project '{project_id}'.")
        #check if subnet exists
        try:
            subnet_client.get(project=project_id, region=region, subnet=subnet_name)
            print(f"Subnet '{subnet_name}' already exists in project '{project_id}' region '{region}'.")
            return
        except Exception:
            print(f"Subnet '{subnet_name}' does not exists in project '{project_id}' region '{region}'.")

    except Exception:
        print(f"VPC network '{network_name}' does not exist in project '{project_id}'. Creating...")

        # Create the custom VPC network
        network_body = compute_v1.Network()
        network_body.name = network_name
        network_body.auto_create_subnetworks = False  # We want to create our own subnet
        request = compute_v1.InsertNetworkRequest(
            project=project_id, network_resource=network_body
        )
        operation = network_client.insert(request=request)

        print(f"Creating VPC network: {network_name}...")

        # Wait for network creation operation to complete
        while operation.operation_type == 'insert' and operation.status!=1:
            time.sleep(5)
            operation = network_client.get_region_operation(project=project_id, region=region, operation=operation.name)
        if operation.status == 1 :
            raise ValueError(f"An error occured during the creation of the network {network_name}: {operation}")
        print(f"VPC network '{network_name}' created successfully.")
    
    # Create the subnet
    subnet_body = compute_v1.Subnetwork()
    subnet_body.name = subnet_name
    subnet_body.ip_cidr_range = ip_range
    subnet_body.region = region
    subnet_body.network = f"projects/{project_id}/global/networks/{network_name}"  # Link subnet to the network
    request = compute_v1.InsertSubnetworkRequest(
        project=project_id, region=region, subnetwork_resource=subnet_body
    )
    operation = subnet_client.insert(request=request)
    print(f"Creating Subnet: {subnet_name} in region {region}...")

    # Wait for subnet creation operation to complete
    while operation.operation_type == 'insert' and operation.status!=1:
            time.sleep(5)
            operation = subnet_client.get_region_operation(project=project_id, region=region, operation=operation.name)

    if operation.status == 1 :
        raise ValueError(f"An error occured during the creation of the subnet {subnet_name}: {operation}")

    print(f"Subnet '{subnet_name}' created successfully in region '{region}'.")


# Example Usage (Integrate with project creation):
if __name__ == "__main__":
    # You should already have a project ID from the create_project_in_folder function.
    # Let's assume you've stored it in a variable called new_project_id
    #new_project_id = "your-project-id"  # Replace with the actual project ID

    # This is only for testing, when you want to execute the code.
#    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "B:\Code\Atkins\credentials.json" # Uncomment if you want to use the json file
    new_project_id = generate_unique_project_id()
    try:
        response = create_project_in_folder(new_project_id)
        print(f"Project created successfully: {response.project_id}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    try:
        response = create_project_in_folder(new_project_id)
        print(f"Project created successfully: {response.project_id}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    try:
        enable_compute_engine_api(new_project_id)
        create_custom_vpc_with_subnet(new_project_id)
        print("Compute Engine and VPC configuration complete.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
