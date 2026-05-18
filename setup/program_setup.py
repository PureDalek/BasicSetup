from __future__ import annotations

import argparse
import json
import queue
import shutil
import subprocess
import threading
import tkinter as tk
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Any

from software_installer import SoftwareInstaller


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIRECTORY.parent
SOFTWARE_CONFIG_PATH = SCRIPT_DIRECTORY / "software.json"
OPTIONAL_CATALOG_PATH = SCRIPT_DIRECTORY / "catalog_extra.json"
BLUEPRINT_CONFIG_PATH = SCRIPT_DIRECTORY / "blueprint.config"
VERSION_PATH = REPOSITORY_ROOT / "VERSION"
UPDATE_CHANNELS = {
    "Stable": "main",
    "Nightly": "codex/gui-version-update-improvements",
}


@dataclass(frozen=True)
class SoftwareItem:
    name: str
    windows_package: str | None
    linux_package: str | None
    linux_repo: str | None = None
    is_snap: bool = False
    from_site: str | None = None


def load_json_config(file_path: Path) -> dict[str, Any]:
    with file_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def save_json_config(file_path: Path, payload: dict[str, Any]) -> None:
    with file_path.open("w", encoding="utf-8") as config_file:
        json.dump(payload, config_file, indent=4)
        config_file.write("\n")


def load_software_catalog(file_path: Path = SOFTWARE_CONFIG_PATH) -> dict[str, SoftwareItem]:
    catalog = load_json_config(file_path)
    return {
        name: SoftwareItem(
            name=name,
            windows_package=config.get("windows_package"),
            linux_package=config.get("linux_package"),
            linux_repo=config.get("linux_repo"),
            is_snap=bool(config.get("is_snap", False)),
            from_site=config.get("from_site"),
        )
        for name, config in sorted(catalog.items(), key=lambda item: item[0].lower())
    }


def parse_software_catalog(catalog: dict[str, Any]) -> dict[str, SoftwareItem]:
    return {
        name: SoftwareItem(
            name=name,
            windows_package=config.get("windows_package"),
            linux_package=config.get("linux_package"),
            linux_repo=config.get("linux_repo"),
            is_snap=bool(config.get("is_snap", False)),
            from_site=config.get("from_site"),
        )
        for name, config in sorted(catalog.items(), key=lambda item: item[0].lower())
    }


def optional_catalog_url(channel_name: str = "Stable") -> str:
    branch_name = update_channel_branch(channel_name)
    return f"https://raw.githubusercontent.com/PureDalek/BasicSetup/{branch_name}/setup/catalog_extra.json"


def load_optional_catalog(channel_name: str = "Stable") -> dict[str, SoftwareItem]:
    try:
        with urllib.request.urlopen(optional_catalog_url(channel_name), timeout=10) as response:
            catalog = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        catalog = load_json_config(OPTIONAL_CATALOG_PATH)

    return parse_software_catalog(catalog)


def load_profiles(file_path: Path = BLUEPRINT_CONFIG_PATH) -> dict[str, list[str]]:
    profiles = load_json_config(file_path)
    return {name: list(packages) for name, packages in profiles.items()}


def save_profiles(profiles: dict[str, list[str]], file_path: Path = BLUEPRINT_CONFIG_PATH) -> None:
    save_json_config(file_path, profiles)


def run_git_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def load_application_version(file_path: Path = VERSION_PATH) -> str:
    if not file_path.exists():
        return "0.0.0-dev"

    version = file_path.read_text(encoding="utf-8").strip()
    return version or "0.0.0-dev"


def get_git_revision() -> str:
    if not shutil.which("git") or not (REPOSITORY_ROOT / ".git").exists():
        return "unknown"

    revision_result = run_git_command(["rev-parse", "--short", "HEAD"])
    if revision_result.returncode != 0:
        return "unknown"

    return revision_result.stdout.strip() or "unknown"


def get_display_version() -> str:
    version = load_application_version()
    revision = get_git_revision()
    if revision == "unknown":
        return f"v{version}"

    return f"v{version} ({revision})"


def update_channel_branch(channel_name: str) -> str:
    return UPDATE_CHANNELS.get(channel_name, UPDATE_CHANNELS["Stable"])


def check_repository_update_status(channel_name: str = "Stable") -> tuple[str, str]:
    if not shutil.which("git"):
        return ("Unavailable", "Git was not found.")

    if not (REPOSITORY_ROOT / ".git").exists():
        return ("Unavailable", "This folder is not a Git checkout.")

    local_version = load_application_version()
    target_branch = update_channel_branch(channel_name)
    branch_result = run_git_command(["branch", "--show-current"])
    branch_name = branch_result.stdout.strip() or "current branch"

    fetch_result = run_git_command(["fetch", "origin", target_branch])
    if fetch_result.returncode != 0:
        return ("Failed", fetch_result.stderr.strip() or "Could not fetch from origin.")

    remote_branch = f"origin/{target_branch}"
    count_result = run_git_command(["rev-list", "--left-right", "--count", f"HEAD...{remote_branch}"])
    if count_result.returncode != 0:
        return ("Failed", count_result.stderr.strip() or f"Could not compare with {remote_branch}.")

    ahead_text, behind_text = count_result.stdout.split()
    ahead_count = int(ahead_text)
    behind_count = int(behind_text)
    channel_label = f"{channel_name} ({target_branch})"

    if behind_count:
        return (
            "Update available",
            f"{behind_count} commit(s) available on {channel_label}. Current version: v{local_version}.",
        )

    if ahead_count:
        return (
            "Up to date",
            f"v{local_version} on {branch_name} is up to date with {channel_label} and {ahead_count} local commit(s) ahead.",
        )

    return ("Up to date", f"v{local_version} on {branch_name} is up to date with {channel_label}.")


def update_repository(channel_name: str = "Stable") -> tuple[str, str]:
    target_branch = update_channel_branch(channel_name)
    remote_branch = f"origin/{target_branch}"
    status, detail = check_repository_update_status(channel_name)
    if status != "Update available":
        return (status, detail)

    current_branch_result = run_git_command(["branch", "--show-current"])
    current_branch = current_branch_result.stdout.strip()
    if current_branch != target_branch:
        local_branch_result = run_git_command(["show-ref", "--verify", "--quiet", f"refs/heads/{target_branch}"])
        if local_branch_result.returncode == 0:
            checkout_result = run_git_command(["checkout", target_branch])
        else:
            checkout_result = run_git_command(["checkout", "-B", target_branch, remote_branch])

        if checkout_result.returncode != 0:
            return ("Failed", checkout_result.stderr.strip() or f"Could not switch to {target_branch}.")

    pull_result = run_git_command(["pull", "--ff-only", "origin", target_branch])
    if pull_result.returncode != 0:
        return ("Failed", pull_result.stderr.strip() or f"Could not fast-forward from {remote_branch}.")

    return ("Updated", f"BasicSetup was updated from {channel_name}. Restart the GUI to load the new version.")


class SetupManager:
    def __init__(
        self,
        master: tk.Tk,
        software_catalog: dict[str, SoftwareItem] | None = None,
        profiles: dict[str, list[str]] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.root = master
        self.software_catalog = software_catalog or load_software_catalog()
        self.profiles = profiles or load_profiles()
        self.dry_run = dry_run
        self.result_queue: queue.Queue[tuple[str, str, str, str]] = queue.Queue()
        self.custom_vars: dict[str, tk.BooleanVar] = {}
        self.installed_status: dict[str, bool] = {}
        self.optional_catalog_loaded = False
        self.optional_catalog_names: set[str] = set()
        self.display_version = get_display_version()
        default_channel = "Nightly" if self._current_branch().startswith("codex/") else "Stable"
        self.update_channel = tk.StringVar(value=default_channel)
        self.selected_profile = tk.StringVar(value=next(iter(self.profiles), ""))
        self.is_installing = False
        self.is_checking_installed = False
        self.is_checking_updates = False

        self.root.title(f"BasicSetup {self.display_version}")
        self.root.geometry("920x640")
        self.root.minsize(820, 560)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self._configure_style()
        self._build_ui()
        self._select_profile(self.selected_profile.get())
        self.root.after(300, self.check_for_updates)
        self.root.after(600, self.check_installed_packages)

    @staticmethod
    def _current_branch() -> str:
        branch_result = run_git_command(["branch", "--show-current"])
        if branch_result.returncode != 0:
            return ""

        return branch_result.stdout.strip()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", foreground="#4b5563")
        style.configure("Version.TLabel", foreground="#4b5563", font=("Segoe UI", 10))
        style.configure("Profile.TButton", padding=(12, 10))
        style.configure("Accent.TButton", padding=(14, 10))
        style.configure("Status.TLabel", foreground="#374151")

    def _build_ui(self) -> None:
        shell = ttk.Frame(self.root, padding=20)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(1, weight=1)

        header = ttk.Frame(shell)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        header.columnconfigure(0, weight=1)

        title_row = ttk.Frame(header)
        title_row.grid(row=0, column=0, sticky="w")

        ttk.Label(title_row, text="BasicSetup", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_row,
            text=self.display_version,
            style="Version.TLabel",
        ).grid(row=0, column=1, sticky="sw", padx=(10, 0), pady=(0, 3))
        ttk.Label(
            header,
            text="Pick a machine profile or build a custom install list for a fresh Windows setup.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.dry_run_label = ttk.Label(
            header,
            text="Dry run enabled" if self.dry_run else "",
            style="Status.TLabel",
        )
        self.dry_run_label.grid(row=0, column=1, sticky="e")

        update_panel = ttk.Frame(header)
        update_panel.grid(row=1, column=1, sticky="e", pady=(4, 0))

        self.update_status_label = ttk.Label(update_panel, text="Update: not checked", style="Status.TLabel")
        self.update_status_label.grid(row=0, column=0, sticky="e", padx=(0, 8))

        self.channel_selector = ttk.Combobox(
            update_panel,
            textvariable=self.update_channel,
            values=tuple(UPDATE_CHANNELS),
            state="readonly",
            width=10,
        )
        self.channel_selector.grid(row=0, column=1, padx=(0, 8))
        self.channel_selector.bind("<<ComboboxSelected>>", lambda _event: self.check_for_updates())

        self.update_check_button = ttk.Button(update_panel, text="Check for Updates", command=self.check_for_updates)
        self.update_check_button.grid(row=0, column=2, padx=(0, 8))

        self.update_button = ttk.Button(
            update_panel,
            text="Update Now",
            command=self.update_now,
            state="disabled",
        )
        self.update_button.grid(row=0, column=3)

        self.profile_panel = ttk.Frame(shell)
        self.profile_panel.grid(row=1, column=0, sticky="nsw", padx=(0, 18))
        self.profile_panel.columnconfigure(0, weight=1)
        self._build_profile_panel()

        content = ttk.Frame(shell)
        content.grid(row=1, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self.tabs = ttk.Notebook(content)
        self.tabs.grid(row=0, column=0, sticky="nsew")

        self.profile_tab = ttk.Frame(self.tabs, padding=12)
        self.custom_tab = ttk.Frame(self.tabs, padding=12)
        self.catalog_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.profile_tab, text="Profile")
        self.tabs.add(self.custom_tab, text="Custom")
        self.tabs.add(self.catalog_tab, text="Catalog")

        self._build_package_table(self.profile_tab)
        self._build_custom_tab()
        self._build_catalog_tab()

        action_bar = ttk.Frame(content)
        action_bar.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        action_bar.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(action_bar, text="Ready", style="Status.TLabel")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.install_button = ttk.Button(
            action_bar,
            text="Install Selected",
            command=self.install_selected_packages,
            style="Accent.TButton",
        )
        self.install_button.grid(row=0, column=1, sticky="e")

    def _build_profile_panel(self) -> None:
        for child in self.profile_panel.winfo_children():
            child.destroy()

        ttk.Label(self.profile_panel, text="Profiles", font=("Segoe UI", 12, "bold")).grid(
            row=0,
            column=0,
            sticky="w",
        )

        for index, profile_name in enumerate(self.profiles, start=1):
            button = ttk.Radiobutton(
                self.profile_panel,
                text=profile_name,
                value=profile_name,
                variable=self.selected_profile,
                command=lambda name=profile_name: self._select_profile(name),
                style="Profile.TButton",
            )
            button.grid(row=index, column=0, sticky="ew", pady=(8, 0))

        action_start_row = len(self.profiles) + 1
        ttk.Separator(self.profile_panel).grid(row=action_start_row, column=0, sticky="ew", pady=16)
        ttk.Button(
            self.profile_panel,
            text="Use Custom Selection",
            command=self._select_custom_tab,
            style="Profile.TButton",
        ).grid(row=action_start_row + 1, column=0, sticky="ew")
        ttk.Button(
            self.profile_panel,
            text="Save Custom as Profile",
            command=self.save_custom_profile,
            style="Profile.TButton",
        ).grid(row=action_start_row + 2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(
            self.profile_panel,
            text="Delete Profile",
            command=self.delete_selected_profile,
            style="Profile.TButton",
        ).grid(row=action_start_row + 3, column=0, sticky="ew", pady=(8, 0))
        self.installed_check_button = ttk.Button(
            self.profile_panel,
            text="Check Installed",
            command=self.check_installed_packages,
            style="Profile.TButton",
        )
        self.installed_check_button.grid(row=action_start_row + 4, column=0, sticky="ew", pady=(8, 0))

    def _build_package_table(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        self.profile_title = ttk.Label(parent, text="", font=("Segoe UI", 14, "bold"))
        self.profile_title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        columns = ("package", "windows", "linux", "status")
        self.package_table = ttk.Treeview(parent, columns=columns, show="headings", selectmode="none")
        self.package_table.heading("package", text="Software")
        self.package_table.heading("windows", text="Windows package")
        self.package_table.heading("linux", text="Linux package")
        self.package_table.heading("status", text="Status")
        self.package_table.column("package", width=210, minwidth=170)
        self.package_table.column("windows", width=170, minwidth=130)
        self.package_table.column("linux", width=160, minwidth=120)
        self.package_table.column("status", width=140, minwidth=110)
        self.package_table.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.package_table.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.package_table.configure(yscrollcommand=scrollbar.set)

    def _build_custom_tab(self) -> None:
        self.custom_tab.columnconfigure(0, weight=1)
        self.custom_tab.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.custom_tab)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.columnconfigure(0, weight=1)

        ttk.Label(toolbar, text="Custom software", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(toolbar, text="Select All", command=self._select_all_custom).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(toolbar, text="Clear", command=self._clear_custom).grid(row=0, column=2, padx=(8, 0))

        canvas = tk.Canvas(self.custom_tab, highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.custom_tab, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        checklist = ttk.Frame(canvas)
        self.custom_checklist = checklist
        canvas_window = canvas.create_window((0, 0), window=checklist, anchor="nw")

        def resize_canvas(event: tk.Event) -> None:
            canvas.itemconfigure(canvas_window, width=event.width)

        canvas.bind("<Configure>", resize_canvas)
        checklist.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))

        self._refresh_custom_checklist()

    def _refresh_custom_checklist(self) -> None:
        for child in self.custom_checklist.winfo_children():
            child.destroy()

        for row_index, software_name in enumerate(self.software_catalog):
            variable = self.custom_vars.setdefault(software_name, tk.BooleanVar(value=False))
            item = self.software_catalog[software_name]
            label = f"{software_name}    Windows: {item.windows_package or 'manual'}    Linux: {item.linux_package or 'manual'}"
            ttk.Checkbutton(self.custom_checklist, text=label, variable=variable).grid(
                row=row_index,
                column=0,
                sticky="w",
                pady=3,
            )

    def _build_catalog_tab(self) -> None:
        self.catalog_tab.columnconfigure(0, weight=1)
        self.catalog_tab.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.catalog_tab)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.columnconfigure(0, weight=1)

        ttk.Label(toolbar, text="Software catalog", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        self.catalog_load_button = ttk.Button(toolbar, text="Load More Catalog", command=self.load_more_catalog)
        self.catalog_load_button.grid(row=0, column=1, padx=(8, 0))
        ttk.Button(toolbar, text="Add Selected to Custom", command=self.add_catalog_selection_to_custom).grid(
            row=0,
            column=2,
            padx=(8, 0),
        )

        columns = ("package", "windows", "linux", "status")
        self.catalog_table = ttk.Treeview(self.catalog_tab, columns=columns, show="headings", selectmode="extended")
        self.catalog_table.heading("package", text="Software")
        self.catalog_table.heading("windows", text="Windows package")
        self.catalog_table.heading("linux", text="Linux package")
        self.catalog_table.heading("status", text="Catalog")
        self.catalog_table.column("package", width=210, minwidth=170)
        self.catalog_table.column("windows", width=170, minwidth=130)
        self.catalog_table.column("linux", width=160, minwidth=120)
        self.catalog_table.column("status", width=140, minwidth=110)
        self.catalog_table.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.catalog_tab, orient="vertical", command=self.catalog_table.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.catalog_table.configure(yscrollcommand=scrollbar.set)
        self._render_catalog_rows()

    def _render_catalog_rows(self) -> None:
        self.catalog_table.delete(*self.catalog_table.get_children())
        for software_name, item in self.software_catalog.items():
            catalog_status = "Optional" if software_name in self.optional_catalog_names else "Basic"
            self.catalog_table.insert(
                "",
                "end",
                iid=software_name,
                values=(
                    software_name,
                    item.windows_package or "manual",
                    item.linux_package or "manual",
                    catalog_status,
                ),
            )

    def _select_profile(self, profile_name: str) -> None:
        self.tabs.select(self.profile_tab)
        package_names = self.profiles.get(profile_name, [])
        self._ensure_packages_available(package_names)
        self.profile_title.configure(text=f"{profile_name} setup ({len(package_names)} apps)")
        self._render_package_rows(package_names)

    def _select_custom_tab(self) -> None:
        self.tabs.select(self.custom_tab)
        self.status_label.configure(text="Choose custom software, then install selected.")

    def _select_all_custom(self) -> None:
        for variable in self.custom_vars.values():
            variable.set(True)

    def _clear_custom(self) -> None:
        for variable in self.custom_vars.values():
            variable.set(False)

    def load_more_catalog(self) -> None:
        try:
            optional_catalog = load_optional_catalog(self.update_channel.get())
        except Exception as error:
            messagebox.showerror("Catalog", f"Could not load optional catalog: {error}")
            return

        self.software_catalog.update(optional_catalog)
        self.software_catalog = dict(sorted(self.software_catalog.items(), key=lambda item: item[0].lower()))
        self.optional_catalog_loaded = True
        self.optional_catalog_names.update(optional_catalog)
        self._refresh_custom_checklist()
        self._render_catalog_rows()
        self.catalog_load_button.configure(state="disabled")
        self.status_label.configure(text=f"Loaded {len(optional_catalog)} optional catalog apps.")

    def add_catalog_selection_to_custom(self) -> None:
        selected_items = self.catalog_table.selection()
        if not selected_items:
            messagebox.showwarning("Catalog", "Select one or more catalog apps first.")
            return

        for software_name in selected_items:
            self.custom_vars.setdefault(software_name, tk.BooleanVar(value=False)).set(True)

        self.tabs.select(self.custom_tab)
        self.status_label.configure(text=f"Added {len(selected_items)} catalog app(s) to custom selection.")

    def save_custom_profile(self) -> None:
        package_names = [name for name, variable in self.custom_vars.items() if variable.get()]
        if not package_names:
            messagebox.showwarning("Profiles", "Select custom software before saving a profile.")
            return

        profile_name = simpledialog.askstring("Save Profile", "Profile name:", parent=self.root)
        if not profile_name:
            return

        profile_name = profile_name.strip()
        if not profile_name:
            messagebox.showwarning("Profiles", "Profile name cannot be empty.")
            return

        if profile_name in self.profiles and not messagebox.askyesno(
            "Save Profile",
            f"Replace the existing '{profile_name}' profile?",
        ):
            return

        self.profiles[profile_name] = package_names
        save_profiles(self.profiles)
        self.selected_profile.set(profile_name)
        self._build_profile_panel()
        self._select_profile(profile_name)
        self.status_label.configure(text=f"Saved profile '{profile_name}' to blueprint.config.")

    def delete_selected_profile(self) -> None:
        protected_profiles = {"Developer", "Games", "AI"}
        profile_name = self.selected_profile.get()
        if profile_name in protected_profiles:
            messagebox.showwarning("Profiles", f"'{profile_name}' is a built-in profile and cannot be deleted.")
            return

        if profile_name not in self.profiles:
            return

        if not messagebox.askyesno("Delete Profile", f"Delete the '{profile_name}' profile?"):
            return

        del self.profiles[profile_name]
        save_profiles(self.profiles)
        next_profile = next(iter(self.profiles), "")
        self.selected_profile.set(next_profile)
        self._build_profile_panel()
        if next_profile:
            self._select_profile(next_profile)
        self.status_label.configure(text=f"Deleted profile '{profile_name}' from blueprint.config.")

    def _render_package_rows(self, package_names: list[str]) -> None:
        self.package_table.delete(*self.package_table.get_children())
        for package_name in package_names:
            item = self.software_catalog.get(package_name)
            if item is None:
                self.package_table.insert(
                    "",
                    "end",
                    iid=package_name,
                    values=(package_name, "missing", "missing", "Missing catalog entry"),
                )
                continue

            install_status = "Installed" if self.installed_status.get(package_name) else "Ready"
            self.package_table.insert(
                "",
                "end",
                iid=package_name,
                values=(
                    package_name,
                    item.windows_package or "manual",
                    item.linux_package or "manual",
                    install_status,
                ),
            )
        self.status_label.configure(text=f"{len(package_names)} packages selected.")

    def _ensure_packages_available(self, package_names: list[str]) -> None:
        missing_packages = [package_name for package_name in package_names if package_name not in self.software_catalog]
        if not missing_packages:
            return

        optional_catalog = load_optional_catalog(self.update_channel.get())
        self.software_catalog.update(optional_catalog)
        self.software_catalog = dict(sorted(self.software_catalog.items(), key=lambda item: item[0].lower()))
        self.optional_catalog_loaded = True
        self.optional_catalog_names.update(optional_catalog)
        self._refresh_custom_checklist()
        self._render_catalog_rows()

    def _installer_for(self, package_name: str) -> SoftwareInstaller:
        item = self.software_catalog[package_name]
        return SoftwareInstaller(
            software_name=item.name,
            windows_package=item.windows_package,
            linux_package=item.linux_package,
            linux_repo=item.linux_repo,
            is_snap=item.is_snap,
            from_site=item.from_site,
        )

    def _selected_package_names(self) -> list[str]:
        if self.tabs.select() == str(self.custom_tab):
            return [name for name, variable in self.custom_vars.items() if variable.get()]

        return list(self.profiles.get(self.selected_profile.get(), []))

    def install_selected_packages(self) -> None:
        if self.is_installing:
            return

        package_names = self._selected_package_names()
        if not package_names:
            messagebox.showwarning("Nothing selected", "Select at least one package to install.")
            return

        self.is_installing = True
        self.install_button.configure(state="disabled")
        self.status_label.configure(text="Installing selected packages...")
        self.profile_title.configure(text=f"Selected setup ({len(package_names)} apps)")
        self.tabs.select(self.profile_tab)
        self._render_package_rows(package_names)

        worker = threading.Thread(target=self._install_packages, args=(package_names,), daemon=True)
        worker.start()
        self.root.after(100, self._drain_result_queue)

    def _install_packages(self, package_names: list[str]) -> None:
        for package_name in package_names:
            if self.installed_status.get(package_name):
                self.result_queue.put(("package", package_name, "Skipped", "Already installed"))
                continue

            self.result_queue.put(("package", package_name, "Installing", ""))

            try:
                if not self.dry_run:
                    self._installer_for(package_name).install()
                    self.installed_status[package_name] = True
                self.result_queue.put(("package", package_name, "Done", ""))
            except Exception as error:
                self.result_queue.put(("package", package_name, "Failed", str(error)))

        self.result_queue.put(("install", "", "Complete", ""))

    def check_installed_packages(self) -> None:
        if self.is_checking_installed:
            return

        self.is_checking_installed = True
        self.installed_check_button.configure(state="disabled")
        self.status_label.configure(text="Checking installed packages...")

        worker = threading.Thread(target=self._check_installed_packages, daemon=True)
        worker.start()
        self.root.after(100, self._drain_result_queue)

    def _check_installed_packages(self) -> None:
        for package_name in self.software_catalog:
            try:
                is_installed = self._installer_for(package_name).is_installed()
                detail = "Installed" if is_installed else "Not installed"
                self.result_queue.put(("installed", package_name, detail, ""))
            except Exception as error:
                self.result_queue.put(("installed", package_name, "Unknown", str(error)))

        self.result_queue.put(("installed", "", "Complete", ""))

    def check_for_updates(self) -> None:
        if self.is_checking_updates:
            return

        self.is_checking_updates = True
        self.update_check_button.configure(state="disabled")
        self.update_button.configure(state="disabled")
        self.channel_selector.configure(state="disabled")
        self.update_status_label.configure(text=f"Update: checking {self.update_channel.get()}...")

        worker = threading.Thread(target=self._check_for_updates, daemon=True)
        worker.start()
        self.root.after(100, self._drain_result_queue)

    def _check_for_updates(self) -> None:
        status, detail = check_repository_update_status(self.update_channel.get())
        self.result_queue.put(("update-check", "", status, detail))

    def update_now(self) -> None:
        if self.is_checking_updates:
            return

        self.is_checking_updates = True
        self.update_check_button.configure(state="disabled")
        self.update_button.configure(state="disabled")
        self.channel_selector.configure(state="disabled")
        self.update_status_label.configure(text=f"Update: updating from {self.update_channel.get()}...")

        worker = threading.Thread(target=self._update_now, daemon=True)
        worker.start()
        self.root.after(100, self._drain_result_queue)

    def _update_now(self) -> None:
        status, detail = update_repository(self.update_channel.get())
        self.result_queue.put(("update-apply", "", status, detail))

    def _drain_result_queue(self) -> None:
        while True:
            try:
                event_type, package_name, status, detail = self.result_queue.get_nowait()
            except queue.Empty:
                break

            if event_type == "install" and status == "Complete":
                self.is_installing = False
                self.install_button.configure(state="normal")
                self.status_label.configure(text="Installation run finished.")
                messagebox.showinfo("BasicSetup", "Installation run finished. Check package statuses for failures.")
                continue

            if event_type == "installed" and status == "Complete":
                self.is_checking_installed = False
                self.installed_check_button.configure(state="normal")
                self.status_label.configure(text="Installed package check finished.")
                self._render_package_rows(self._selected_package_names())
                continue

            if event_type == "installed":
                self.installed_status[package_name] = status == "Installed"
                if package_name in self.package_table.get_children():
                    values = list(self.package_table.item(package_name, "values"))
                    values[3] = status if not detail else f"{status}: {detail}"
                    self.package_table.item(package_name, values=values)
                continue

            if event_type in {"update-check", "update-apply"}:
                self.is_checking_updates = False
                self.update_check_button.configure(state="normal")
                self.channel_selector.configure(state="readonly")
                self.update_button.configure(state="normal" if status == "Update available" else "disabled")
                self.update_status_label.configure(text=f"Update: {status}")
                self.status_label.configure(text=detail)
                if event_type == "update-apply":
                    messagebox.showinfo("BasicSetup update", detail)
                continue

            if event_type == "package" and package_name in self.package_table.get_children():
                values = list(self.package_table.item(package_name, "values"))
                values[3] = status if not detail else f"{status}: {detail}"
                self.package_table.item(package_name, values=values)
            self.status_label.configure(text=f"{package_name}: {status}")

        if self.is_installing or self.is_checking_installed or self.is_checking_updates:
            self.root.after(100, self._drain_result_queue)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the BasicSetup GUI.")
    parser.add_argument("--dry-run", action="store_true", help="Show install flow without running package managers.")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    root = tk.Tk()
    SetupManager(root, dry_run=arguments.dry_run)
    root.mainloop()


if __name__ == "__main__":
    main()
