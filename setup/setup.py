#setup.py
import tkinter as tk
import json
from software_installer import SoftwareInstaller  # Make sure this import is correct

class SetupManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Setup Selection")
        self.master.geometry("400x200")  # Set the window size to 400x200
        self.software_config = self.load_software_config("software.json")
        self.blueprint = self.load_software_config("blueprint.config")

        tk.Label(self.master, text="Choose your setup:", font=("Arial", 14)).pack(pady=20)
        
        for blueprint_name in self.blueprint:
            button = tk.Button(self.master, text=f"{blueprint_name} Setup", command=lambda name=blueprint_name: self.run_setup(name), width=20)
            button.pack(pady=10)

    def run_setup(self, blueprint_name):
        for software_name, config in self.software_config.items():
            if software_name in self.blueprint[blueprint_name]:
                installer = SoftwareInstaller(software_name, config["windows_package"], config["linux_package"])
                installer.install()

    @staticmethod
    def load_software_config(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

def main():
    root = tk.Tk()
    app = SetupManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()

