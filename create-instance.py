from google.cloud import compute_v1

def create_instance_from_cross_project_machine_image_with_sa(
    project_id,
    zone,
    instance_name,
    machine_image_project,
    machine_image_name,
    service_account_email,
    subnet,
    machine_type="e2-medium",
    external_access=True,
):
    """
    Creates a Compute Engine instance from a machine image in a different project,
    specifying a service account and subnet.

    Args:
        project_id: Project ID where the instance will be created.
        zone: Zone in which to create the instance.
        instance_name: Name of the instance.
        machine_image_project: Project ID where the machine image is located.
        machine_image_name: Name of the machine image.
        service_account_email: Email address of the service account to use.
        subnet: Name of the subnet to use.
        machine_type: Machine type of the instance. Defaults to "e2-medium".
        external_access: True to assign an external IP address, False otherwise.
    """

    instance_client = compute_v1.InstancesClient()

    # Construct the full machine image URI.
    machine_image_uri = f"projects/{machine_image_project}/global/machineImages/{machine_image_name}"

    # Configure the machine image disk.
    machine_image_disk = compute_v1.AttachedDisk()
    machine_image_disk.source_machine_image = machine_image_uri
    machine_image_disk.boot = True
    machine_image_disk.auto_delete = True
    machine_image_disk.type_ = compute_v1.AttachedDisk.Type.PERSISTENT.name

    # Configure the network interface.
    network_interface = compute_v1.NetworkInterface()
    network_interface.network = f"projects/{project_id}/global/networks/default" #network is default in the gcloud command.
    network_interface.subnetwork = f"projects/{project_id}/regions/{zone[:-2]}/subnetworks/{subnet}"

    if external_access:
        access = compute_v1.AccessConfig()
        access.type_ = compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT.name
        network_interface.access_configs = [access]

    # Configure the service account.
    service_account = compute_v1.ServiceAccount()
    service_account.email = service_account_email
    service_account.scopes = [
        "https://www.googleapis.com/auth/cloud-platform" #full cloud platform scope, adapt as needed.
    ]

    # Configure the instance.
    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = f"zones/{zone}/machineTypes/{machine_type}"
    instance.disks = [machine_image_disk]
    instance.network_interfaces = [network_interface]
    instance.service_accounts = [service_account]

    # Create the request and send it.
    request = compute_v1.InsertInstanceRequest()
    request.project = project_id
    request.zone = zone
    request.instance_resource = instance

    operation = instance_client.insert(request=request)

    print(f"Instance creation started: {operation.name}")
    operation_client = compute_v1.ZoneOperationsClient()
    operation_client.wait(operation=operation)

    print(f"Instance {instance_name} created in {zone}.")

# Example usage (with service account and subnet):
instance_project_id = "atkins-project-612c"
zone = "us-central1-a"
instance_name = "atkins-test"
machine_image_project_id = "test-metal-358914"
machine_image_name = "flood-analysis"
service_account_email = "277238354570-compute@developer.gserviceaccount.com"
subnet_name = "sub"

create_instance_from_cross_project_machine_image_with_sa(
    instance_project_id,
    zone,
    instance_name,
    machine_image_project_id,
    machine_image_name,
    service_account_email,
    subnet_name,
)