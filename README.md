This streamlit app create a project and X number of VMS under a FOLDER and SUBFOLDER.
The app is meant to run in Cloud Run with IAP enable and will capture username automatically to name all the resources created (projects and VMs)

The ps1 script is meant to be use as a startup script when creating the VMs to automatically mount the second data disk attached the VMs (only support 1 disk)
The source image for the VMs and startup script in the GCS bucket should be store in an existing project and should act as "golden resource". 
The code need to be update with the project ID so the app knows where to find the images and the startup script.
FOLDER and SUBFOLDER value should be modify to your own Org.
GCP hierarchical firewall rules should be use at the FOLDER level

Since Cloud Run use by default the Compute Engine Service Account, permissions should be assign to it so the app can create Projects ; VMs and VPC, some permission include (more might be needed)
Billing Account User
Folder Viewer
Project Creator
Compute instance admin v1
