from google.cloud import billing_v1
from google.cloud import resourcemanager_v3
from google.cloud.resourcemanager_v3 import types
from google.cloud import compute_v1
from google.cloud import service_usage_v1
from google.api_core import operation
#from google.cloud import iam_admin_v1
import uuid
import os
import random
import time
import streamlit as st

# Static variable for the billing account ID
BILLING_ACCOUNT_ID = "billingAccounts/015F68-FEF42E-E10820"  # Replace with your actual billing account ID - new format
TARGET_FOLDER_PATH = ["North America", "atkins"]  # Define the path to the target folder.
ORGANIZATION_ID = "organizations/690423753921"  # Replace with your actual organization id
zone = "us-central1-c"  # Replace with your desired zone
region = "us-central1"  # Replace with your desired region
source_image = "projects/test-metal-358914/global/images/atkins-gold"  # Replace with your source image
network_name = "atkins-custom-vpc"
subnet_name = "subnet1"
ip_range = "172.18.100.0/24"

def find_folder_id_recursive(folder_client, parent, folder_path):
    """
    Recursively finds the folder ID based on the folder path.

    Args:
        folder_client: The resourcemanager_v3.FoldersClient.
        parent: The parent resource (organization or folder) to start the search.
        folder_path: A list of folder names representing the path (e.g., ["North America", "atkins"]).

    Returns:
        The folder ID (full resource name) if found, otherwise None.
    """
    if not folder_path:
        return parent  # return the root folder if the path is empty.

    current_folder_name = folder_path[0]
    list_request = resourcemanager_v3.ListFoldersRequest(
        parent=parent, page_size=100, show_deleted=False
    )
#    print(f"Searching for folder '{current_folder_name}' under parent '{parent}'")  # Debugging
    for folder in folder_client.list_folders(request=list_request):
#        print(f"  Found folder: {folder.display_name} (name: {folder.name})")  # Debugging
        if folder.display_name == current_folder_name:
            # Found the current folder in the path.
            remaining_path = folder_path[1:]  # Get the rest of the path.
            if not remaining_path:
#                print(f"    Found target folder: {folder.name}")  # Debugging
                return folder.name  # This was the last folder in the path.
            else:
                # Recursively search in the child folder.
                return find_folder_id_recursive(folder_client, folder.name, remaining_path)
#    print(f"Folder '{current_folder_name}' not found under '{parent}'")  # Debugging
    return None  # Folder not found at this level.

def create_project_in_folder(project_id):
    """Creates a Google Cloud project inside a specific folder and attaches a billing account."""

    project_client = resourcemanager_v3.ProjectsClient()
    billing_client = billing_v1.CloudBillingClient()
    folder_client = resourcemanager_v3.FoldersClient()

    # Start the search from the organization
    st.markdown(f"**Starting project creation for project ID: {project_id}**")
#    print(f"Starting project creation for project ID: {project_id}")  # Debugging
#    print(f"Using organization ID: {ORGANIZATION_ID}")  # Debugging
    folder_full_id = find_folder_id_recursive(folder_client, ORGANIZATION_ID, TARGET_FOLDER_PATH)

    if folder_full_id is None:
        raise ValueError(f"Folder path '{TARGET_FOLDER_PATH}' not found.")
#    print(f"Found folder ID: {folder_full_id}")  # Debugging

    project = resourcemanager_v3.Project()
    project.project_id = project_id
    project.display_name = project_id
    project.parent = folder_full_id # new code
    operation = project_client.create_project(project=project)

    try:
        response = operation.result()
        # Get the project number from the response
        project_number = response.name.split('/')[1]
    except Exception as e:
        raise ValueError(f"An error occurred during the project creation: {e}")
    st.success(f"Project {response.project_id} created successfully", icon="✅")
    #print(f"Project created successfully : {response.project_id}")  # Debugging
    #print(f"Your Project number is : {project_number}")

    project_name = f"projects/{project_id}"

    # Set Billing account
    try:
        #st.markdown(f"**Attaching billing account to project**")
        billing_client.update_project_billing_info(
            name=project_name, project_billing_info={"billing_account_name": BILLING_ACCOUNT_ID}
        )
        #st.success(f"Billing account attached successfully to {project_name}" , icon="✅")
#        print(f"Billing account attached successfully to {project_name}")
    except Exception as e:
        raise ValueError(f"An error occurred when attaching the billing account: {e}")
    return {"project_id": response.project_id, "project_number": project_number}

def generate_unique_project_id(name_project):
    """Generates a unique project ID."""
    return f"project-{name_project}-{uuid.uuid4().hex[:4]}"

def enable_compute_engine_api(project_id):
    """Enables the Compute Engine API for the specified project."""

    service_client = service_usage_v1.ServiceUsageClient()
    service_name = f"projects/{project_id}/services/compute.googleapis.com"

    try:
        # Check if the service is already enabled
        get_request = service_usage_v1.GetServiceRequest(name=service_name)
        service = service_client.get_service(request=get_request)
        # if service.state == service_usage_v1.Service.State.ENABLED:
        #     print(f"Compute Engine API is already enabled for project: {project_id}")
        #     return

        # Enable the service
        enable_request = service_usage_v1.EnableServiceRequest(name=service_name)
        operation = service_client.enable_service(request=enable_request)

        st.markdown(f"**Enabling Compute Engine API for project: {project_id}**")
        #print(f"Enabling Compute Engine API for project: {project_id}...")
        response = operation.result()  # Wait for the operation to complete
        st.success(f"Compute Engine API enabled successfully for project: {project_id}", icon="✅")
        return response

    except Exception as e:
        raise ValueError(f"Error enabling Compute Engine API: {e}")

def create_custom_vpc_with_subnet(project_id, region):
    """
    Creates a custom VPC network with a subnet in the specified region.

    Args:
        project_id: The ID of the project.
        region: The region in which to create the subnet (default: us-central1).
    """
    network_client = compute_v1.NetworksClient()
    subnet_client = compute_v1.SubnetworksClient()

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
       # print(f"VPC network '{network_name}' does not exist in project '{project_id}'. Creating...")

        # Create the custom VPC network
        network_body = compute_v1.Network()
        network_body.name = network_name
        network_body.auto_create_subnetworks = False  # We want to create our own subnet
        request = compute_v1.InsertNetworkRequest(
            project=project_id, network_resource=network_body
        )
        operation = network_client.insert(request=request)

        st.markdown(f"**Creating VPC network: {network_name}**")

        # Wait for network creation operation to complete
        operation_client = compute_v1.GlobalOperationsClient()
        while operation.status != compute_v1.Operation.Status.DONE:
            operation = operation_client.wait(
                project=project_id, operation=operation.name, timeout=300
            )
            #print(f"Operation status: {operation.status}")
        if operation.error:
            raise ValueError(f"An error occured during the creation of the network {network_name}: {operation.error}")
        st.success(f"VPC network created successfully.", icon="✅")
        #print(f"VPC network created successfully.")
    
    # Create the subnet
    subnet_body = compute_v1.Subnetwork()
    subnet_body.name = subnet_name
    subnet_body.ip_cidr_range = ip_range
    subnet_body.region = region
    subnet_body.network = f"projects/{project_id}/global/networks/{network_name}"  # Link subnet to the network
    request = compute_v1.InsertSubnetworkRequest(project=project_id, region=region, subnetwork_resource=subnet_body)
    operation = subnet_client.insert(request=request)
    #st.markdown(f"**Creating Subnet in region {region}**")

    # Wait for subnet creation operation to complete
    operation_client = compute_v1.RegionOperationsClient()
    while operation.status != compute_v1.Operation.Status.DONE:
        operation = operation_client.wait(
            project=project_id, region=region, operation=operation.name, timeout=300
        )
        #print(f"Operation status: {operation.status}")
    if operation.error:
        raise ValueError(f"An error occured during the creation of the subnet {subnet_name}: {operation.error}")

    #st.success(f"Subnet created successfully in region '{region}'.", icon="✅")

def create_instance(project_id, zone, service_account_email, instance_name, machine_type, subnet_name, source_image, disk_size_gb, disk_type, second_disk_size_gb, second_disk_type):
    """
    Creates a Google Compute Engine instance with specified configurations.

    Args:
        project_id: The ID of the project.
        zone: The zone in which to create the instance.
        instance_name: The name of the instance.
        machine_type: The machine type for the instance.
        subnet_name: The name of the subnet to use.
        source_image: The source image for the boot disk.
        disk_size_gb: The size of the boot disk in GB.
        disk_type: The type of the boot disk.
        second_disk_size_gb: The size of the second disk in GB.
        second_disk_type: The type of the second disk.
    """
    instance_client = compute_v1.InstancesClient()
    disk_client = compute_v1.DisksClient()
    zone_operations_client = compute_v1.ZoneOperationsClient()

    # Check if the instance already exists
    try:
        instance_client.get(project=project_id, zone=zone, instance=instance_name)
        print(f"Instance '{instance_name}' already exists in project '{project_id}' zone '{zone}'.")
        return
    except Exception:
        print(f"Instance '{instance_name}' does not exist in project '{project_id}' zone '{zone}'. Creating...")

    # Define the boot disk configuration
    boot_disk = compute_v1.AttachedDisk()
    initialize_params = compute_v1.AttachedDiskInitializeParams()
    initialize_params.source_image = source_image
#    print(f"{initialize_params.source_image}")
    initialize_params.disk_size_gb = disk_size_gb
    initialize_params.disk_type = disk_type
    boot_disk.initialize_params = initialize_params
    boot_disk.auto_delete = True
    boot_disk.boot = True
    boot_disk.device_name = instance_name
#    print(f"{boot_disk.device_name}")

    # Define the second disk configuration
    second_disk = compute_v1.AttachedDisk()
    second_disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
    second_disk.initialize_params.disk_size_gb = second_disk_size_gb
    second_disk.initialize_params.disk_type = second_disk_type
    second_disk.auto_delete = True
    random_digits = str(random.randint(100, 999))
    second_disk_name = f"disk-{random_digits}"  # Add the 3-digit number to the disk name
    second_disk.initialize_params.disk_name = second_disk_name
#    print(f"{second_disk.device_name}")

    # Define the network interface configuration
    print("Define the network interface configuration")
    network_interface = compute_v1.NetworkInterface()
    network_interface.subnetwork = subnet_name
#     access_config = compute_v1.AccessConfig()
#     access_config.type_ = compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT.name
#     access_config.name = "External NAT"
#     access_config.network_tier = compute_v1.AccessConfig.NetworkTier.PREMIUM.name
# #    print(f"{access_config.network_tier}")
#     network_interface.access_configs = [access_config]
# #    print(f"{network_interface.access_configs}")

    # Define the service account configuration
    service_account = compute_v1.ServiceAccount()
    service_account.email = service_account_email
    service_account.scopes = [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/logging.write",
        "https://www.googleapis.com/auth/monitoring.write",
        "https://www.googleapis.com/auth/service.management.readonly",
        "https://www.googleapis.com/auth/servicecontrol",
        "https://www.googleapis.com/auth/trace.append",
    ]

    # Define the metadata configuration
    metadata = compute_v1.Metadata()
    metadata.items = [
        compute_v1.Items(key="enable-osconfig", value="TRUE"),
        compute_v1.Items(key="enable-oslogin", value="true"),
    ]

    # Define the shielded instance configuration
    shielded_instance_config = compute_v1.ShieldedInstanceConfig()
    shielded_instance_config.enable_integrity_monitoring = True
    shielded_instance_config.enable_secure_boot = False
    shielded_instance_config.enable_vtpm = True

    # Create the instance object
    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = machine_type
    instance.disks = [boot_disk, second_disk]
    instance.network_interfaces = [network_interface]
    instance.service_accounts = [service_account]
    instance.metadata = metadata
    instance.shielded_instance_config = shielded_instance_config
    instance.can_ip_forward = False
    instance.confidential_instance_config = compute_v1.ConfidentialInstanceConfig(enable_confidential_compute=False)
    instance.deletion_protection = False
    instance.display_device = compute_v1.DisplayDevice(enable_display=False)
    instance.key_revocation_action_type = "NONE"
    instance.labels = {
        "goog-ops-agent-policy": "v2-x86-template-1-4-0",
        "goog-ec-src": "vm_add-rest",
    }
    instance.reservation_affinity = compute_v1.ReservationAffinity(consume_reservation_type="ANY_RESERVATION")
    instance.scheduling = compute_v1.Scheduling(automatic_restart=True, on_host_maintenance="MIGRATE", provisioning_model="STANDARD")
    
    # Add the network tag "rdp"
    instance.tags = compute_v1.Tags(items=["rdp"])

    instance.guest_accelerators = []
    instance.instance_encryption_key = compute_v1.CustomerEncryptionKey()
    instance.params = compute_v1.InstanceParams(resource_manager_tags={})
    instance.zone = f"projects/{project_id}/zones/{zone}"

    # Create the instance creation request
    request = compute_v1.InsertInstanceRequest(
        project=project_id, zone=zone, instance_resource=instance
    )

    # Execute the instance creation request
    operation = instance_client.insert(request=request)
    print(f"Creating instance {instance_name} in {zone}...")
    
    # Wait for the operation to complete.
    operation_client = compute_v1.ZoneOperationsClient()

    while operation.status != compute_v1.Operation.Status.DONE:
        operation = operation_client.wait(
            project=project_id, zone=zone, operation=operation.name, timeout=300
        )
        #print(f"Operation status: {operation.status}")

    if operation.error:
        st.error(f"Error creating instance:")
    else:
        st.success(f"Instance created successfully.", icon="✅")
        #print(f"Instance {instance_name} created successfully.")
        #print(f"Instance link: {operation.target_link}")   

def disable():
    st.session_state.disabled = True

# Example Usage (Integrate with project creation):
if __name__ == "__main__":
    logo = "logo.png"
    st.image(logo)
    st.title('\n''Atkins Flood App''\n')
    st.header('1. Pre-Requisite')
    st.markdown("- Ensure you have a @hazserv.com account")
    st.markdown("- Download and install the [IAP RDP Client](https://googlecloudplatform.github.io/iap-desktop/) to access your VM")
    st.markdown("- Create your environment using the form below")
    st.markdown("- Follow the guide here to connect to your VMs")
    st.context.headers
    st.header('2. Project & VMs creation')
    # Initialize disabled for form_submit_button to False
    if "disabled" not in st.session_state:
        st.session_state.disabled = False
    with st.form('my_form',enter_to_submit=False):    
        # Input widgets
        name_project = st.text_input('Enter your username:',"ie:username@hazserv.com", max_chars=15)
        vm_size = st.selectbox('Choose your VM size', ['Small', 'Medium', 'Large'])
        vm_numbers = st.select_slider('How many VMs do you need', ['1', '2', '3', '4', '5'])
        # Every form must have a submit button
        submitted = st.form_submit_button('Submit', on_click=disable, disabled=st.session_state.disabled)

# Start Code Execution when button is clicked.
        if submitted:
            new_project_id = generate_unique_project_id(name_project)
            instance_name = f"instance-{uuid.uuid4().hex[:4]}"  # Replace with your desired instance name
            machine_type = f"projects/{new_project_id}/zones/{zone}/machineTypes/e2-medium"  # Replace with your desired machine type
            compute_subnet_name = f"projects/{new_project_id}/regions/us-central1/subnetworks/{subnet_name}"  
            disk_size_gb = 50
            disk_type = f"projects/{new_project_id}/zones/{zone}/diskTypes/pd-balanced"
            second_disk_size_gb = 300
            second_disk_type = f"projects/{new_project_id}/zones/{zone}/diskTypes/pd-balanced"
            try:
                response = create_project_in_folder(new_project_id)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                st.error(f"An unexpected error occurred when creating project: {e}")
            try:
                enable_compute_engine_api(new_project_id)
                time.sleep(25)
                create_custom_vpc_with_subnet(new_project_id, region);
                p_number = response["project_number"];
                service_account_email = f"{p_number}-compute@developer.gserviceaccount.com"
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            try:
                time.sleep(15)
                # Loop to create multiple instances
                for i in range(int(vm_numbers)):
                    instance_name = f"instance-{name_project}-{i}-{uuid.uuid4().hex[:4]}"  # Unique instance name
                    create_instance(new_project_id, zone, service_account_email, instance_name, machine_type, compute_subnet_name, source_image, disk_size_gb, disk_type, second_disk_size_gb, second_disk_type)
                st.markdown("**Done !**")
                st.markdown(f"Sign-in using your @hazserv.com account and use project ID: {new_project_id}")
            except Exception as e:
                st.error(f"An error occurred instance creation: {e}")
