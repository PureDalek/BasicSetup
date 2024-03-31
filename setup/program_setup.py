from tkinter import Button, Label, Toplevel, Checkbutton, IntVar, StringVar, Tk
import json
from software_installer import SoftwareInstaller  # Make sure this import is correct

class SetupManager:
    def __init__(self, master):
        self.tk = master
        self.tk.title("Setup Selection")
        self.tk.geometry("400x200")  # Set the window size to 400x200
        self.software_config = self.load_software_config("software.json")
        self.blueprint = self.load_software_config("blueprint.config")
        self.checkbuttons = {}

        Label(self.tk, text="Choose your setup:", font=("Arial", 14)).pack(pady=20)
        
        for blueprint_name in self.blueprint:
            button = Button(self.tk, text=f"{blueprint_name} Setup", command=lambda name=blueprint_name: self.run_setup(name), width=20)
            button.pack(pady=10)

        self.openNewWindowButton = Button(self.tk, text="Custom Install", command=self.openNewWindow)
        self.openNewWindowButton.pack(pady=10)

    def run_setup(self, blueprint_name):
        for software_name, config in self.software_config.items():
            if software_name in self.blueprint[blueprint_name]:
                installer = SoftwareInstaller(software_name, config["windows_package"], config["linux_package"])
                installer.install()
        self.done_window(f"{blueprint_name} Installation Completed")
                


    def define_custom(self, instance):
        for software_name in self.software_config.keys():
            var = IntVar()  # Use IntVar for Checkbutton
            cb = Checkbutton(instance, text=software_name, variable=var, onvalue=1, offvalue=0, command=self.save_to_custom_list)
            cb.pack()
            self.checkbuttons[software_name] = var

    def done_window(self,name):
        done_window = Toplevel(self.tk)
        done_window.title(name)
        done_window.geometry(f"200x200")
        button = Button(done_window, text=f"Done", command=done_window.destroy)
        button.pack(pady=10)

    def save_to_custom_list(self):
        # Example of how to access the states
        self.custom_list= []
        for software_name, var in self.checkbuttons.items():
            if var.get() == 1 :
                self.custom_list.append(software_name)
            print(f"{software_name}: {var.get()}")
        print(f"my list: {self.custom_list}")
        self.blueprint["Custom_install"] = self.custom_list
        print(f"my blueprints: {self.blueprint }")

    def openNewWindow(self):
        newWindow = Toplevel(self.tk)
        newWindow.title("New Window")
        size = len(self.software_config.keys()) *40
        newWindow.geometry(f"200x{size}")

        Label(newWindow, text="Select software to install:").pack()
        self.define_custom(newWindow)
        button = Button(newWindow, text=f"Install Marked ", command=lambda name="Custom_install": self.run_setup(name), width=20)
        button.pack(pady=10)
        
    @staticmethod
    def load_software_config(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

def main():
    root = Tk()
    app = SetupManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
