import json
import tkinter as tk
from tkinter import ttk
from software_installer import SoftwareInstaller

class SetupManager:
    def __init__(self, master):
        self.tk = master
        self.tk.title("Setup Selection")
        self.tk.geometry("500x400")
        self.tk.resizable(False, False)

        self.software_config = self.load_software_config("software.json")
        self.blueprint = self.load_software_config("blueprint.config")
        self.checkbuttons = {}

        main_frame = ttk.Frame(self.tk, padding=20)
        main_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(main_frame, text="Choose your setup:", font=("Segoe UI", 14)).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Grid layout for setup buttons
        for i, blueprint_name in enumerate(self.blueprint):
            row, col = divmod(i, 2)
            ttk.Button(main_frame, text=f"{blueprint_name} Setup", command=lambda name=blueprint_name: self.run_setup(name))\
                .grid(row=row+1, column=col, padx=10, pady=5, sticky="ew")

        # Custom install button spans both columns
        ttk.Button(main_frame, text="Custom Install", command=self.open_custom_window)\
            .grid(row=(len(self.blueprint) // 2) + 2, column=0, columnspan=2, pady=15, sticky="ew")

    def run_setup(self, blueprint_name):
        for software_name, config in self.software_config.items():
            if software_name in self.blueprint[blueprint_name]:
                installer = SoftwareInstaller(software_name, config["windows_package"], config["linux_package"])
                installer.install()
        self.show_done_window(f"{blueprint_name} Installation Completed")

    def show_done_window(self, title):
        done_window = tk.Toplevel(self.tk)
        done_window.title(title)
        done_window.geometry("250x100")
        ttk.Label(done_window, text=title, font=("Segoe UI", 12)).pack(pady=10)
        ttk.Button(done_window, text="Close", command=done_window.destroy).pack(pady=10)

    def open_custom_window(self):
        new_window = tk.Toplevel(self.tk)
        new_window.title("Custom Install")
        new_window.geometry("400x400")

        container = ttk.Frame(new_window)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        canvas.pack(side="left", fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        v_scrollbar.pack(side="right", fill="y")

        h_scrollbar = ttk.Scrollbar(new_window, orient="horizontal", command=canvas.xview)
        h_scrollbar.pack(side="bottom", fill="x")

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        scrollable_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        ttk.Label(scrollable_frame, text="Select software to install:", font=("Segoe UI", 12)).grid(row=0, column=0, columnspan=3, pady=10)

        # Grid layout for checkboxes
        for i, software_name in enumerate(self.software_config.keys()):
            var = tk.IntVar()
            row, col = divmod(i, 3)  # 3 columns
            cb = ttk.Checkbutton(scrollable_frame, text=software_name, variable=var, command=self.save_to_custom_list)
            cb.grid(row=row+1, column=col, padx=10, pady=5, sticky="w")
            self.checkbuttons[software_name] = var

        ttk.Button(scrollable_frame, text="Install Marked", command=lambda: self.run_setup("Custom_install"))\
            .grid(row=(len(self.software_config) // 3) + 2, column=0, columnspan=3, pady=15)

    def save_to_custom_list(self):
        self.custom_list = [name for name, var in self.checkbuttons.items() if var.get() == 1]
        self.blueprint["Custom_install"] = self.custom_list

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
