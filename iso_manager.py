import subprocess
import os

class IsoManager:
    def __init__(self):
        self.mounted_drive_letter = None

    def mount_iso(self, iso_path):
        if not os.path.exists(iso_path):
            print(f"Error: ISO file not found at {iso_path}")
            return False

        try:
            # PowerShell command to mount ISO
            # Get-DiskImage -ImagePath "<iso_path>" | Mount-DiskImage
            command = [
                "powershell.exe",
                "-Command",
                f"$drive = Mount-DiskImage -ImagePath \"{iso_path}\" -PassThru; $drive.DriveLetter"
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            drive_letter = result.stdout.strip()
            if drive_letter:
                self.mounted_drive_letter = drive_letter
                print(f"Successfully mounted {iso_path} to drive {drive_letter}:")
                return True
            else:
                print(f"Failed to mount ISO: {iso_path}. Output: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"PowerShell command failed: {e}")
            print(f"Stderr: {e.stderr}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def dismount_iso(self):
        if not self.mounted_drive_letter:
            print("No ISO currently mounted by this manager.")
            return False

        try:
            # PowerShell command to dismount ISO
            # Dismount-DiskImage -DriveLetter <drive_letter>
            command = [
                "powershell.exe",
                "-Command",
                f"Dismount-DiskImage -DriveLetter {self.mounted_drive_letter}"
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            if result.returncode == 0:
                print(f"Successfully dismounted drive {self.mounted_drive_letter}:")
                self.mounted_drive_letter = None
                return True
            else:
                print(f"Failed to dismount drive {self.mounted_drive_letter}: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"PowerShell command failed: {e}")
            print(f"Stderr: {e.stderr}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def get_mounted_drive_letter(self):
        return self.mounted_drive_letter
