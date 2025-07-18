# ps-disk.ps1 - Simplified for Google Cloud startup script
# This script formats Disk 1 as D: with label "Data", NTFS, 4KB allocation unit.
# It expects Disk 1 to be a new, raw, or unformatted disk.
# WARNING: This script will format the disk and all data on it will be lost.

$ErrorActionPreference = "Stop" # Exit on any cmdlet error

# --- Script Logic ---

# 1. Get the disk (Disk 1)
# If Get-Disk fails (e.g., disk not found), script will stop due to $ErrorActionPreference.
$disk = Get-Disk -Number 1

# 2. Bring online if offline
if ($disk.IsOffline) {
    Set-Disk -Number 1 -IsOffline $false
    # Refresh disk object to get updated PartitionStyle after bringing online
    $disk = Get-Disk -Number 1
}

# 3. Verify disk is raw or unformatted. If not, exit to prevent data loss.
if ($disk.PartitionStyle -ne 'Raw' -and $disk.PartitionStyle -ne 'Unformatted') {
    # Disk is not in the expected initial state (raw/unformatted).
    # This could mean it's already partitioned, contains data, or is an OS disk.
    # For a startup script intended for a new data disk, this is an error condition.
    exit 1 # Indicate failure: disk not raw/unformatted
}

# 4. Initialize Disk (it's confirmed to be Raw or Unformatted at this point)
# Choose GPT for disks larger than 2TB, MBR for smaller.
$partitionStyleToUse = if ($disk.Size -gt 2TB) { "GPT" } else { "MBR" }
Initialize-Disk -Number 1 -PartitionStyle $partitionStyleToUse

# 5. Create New Partition (using the entire disk)
# We need the partition object for Format-Volume and Set-Partition.
$newPartition = New-Partition -DiskNumber 1 -UseMaximumSize

# 6. Format the Volume
# FileSystem: NTFS, Label: Data, AllocationUnitSize: 4096
Format-Volume -Partition $newPartition -FileSystem "NTFS" -NewFileSystemLabel "Data" -AllocationUnitSize 4096 -Force -Confirm:$false

# 7. Assign Drive Letter (D)
Set-Partition -InputObject $newPartition -NewDriveLetter 'D'

exit 0 # Success