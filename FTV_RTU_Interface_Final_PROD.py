import os
import time
import threading
import subprocess
import customtkinter
from tkinter import Text, Scrollbar, END
from FtvAppsConfig import FtvAppsConfigurations

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.app_running = False
        self.stopwatch_running = False
        self.is_stopwatch_started = False
        self.log_capturing = False
        self.stopwatch_start_time = 0
        self.iteration_count = 0
        self.iteration_times = []
        self.log_capturing = False
        self.log_capture_thread = None

        self.title("RTU Interface")
        self.geometry(f"{1100}x{800}+0+0")
        self.resizable(True, True)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=12, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(12, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="RTU Interface", font=customtkinter.CTkFont(size=20, weight="bold"), text_color="red")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_Clear_Logs = customtkinter.CTkButton(self.sidebar_frame, text="Clear Logs", command=self.clear_logs)
        self.sidebar_Clear_Logs.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_Start_Logs = customtkinter.CTkButton(self.sidebar_frame, text="Start Logs", command=self.start_logs)
        self.sidebar_Start_Logs.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_Save_Logs = customtkinter.CTkButton(self.sidebar_frame, text="Save Logs", command=self.save_logs)
        self.sidebar_Save_Logs.grid(row=3, column=0, padx=20, pady=10)
        self.sidebar_Force_Close = customtkinter.CTkButton(self.sidebar_frame, text="Force Stop", command=self.force_stop_app_button_click)
        self.sidebar_Force_Close.grid(row=4, column=0, padx=20, pady=10)
        self.sidebar_Download = customtkinter.CTkButton(self.sidebar_frame, text="Download", command=self.download_selected_apps)
        self.sidebar_Download.grid(row=5, column=0, padx=20, pady=10)
        self.sidebar_Uninstall = customtkinter.CTkButton(self.sidebar_frame, text="Uninstall", command=self.uninstall_selected_app)
        self.sidebar_Uninstall.grid(row=6, column=0, padx=20, pady=10)
        self.sidebar_reset = customtkinter.CTkButton(self.sidebar_frame, text="Reset", command=self.reset_to_defaults)
        self.sidebar_reset.grid(row=7, column=0, padx=20, pady=10)
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=10, column=0, padx=20, pady=(10, 0))
        self.scaling_optionmenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%"], command=self.change_scaling_event)
        self.scaling_optionmenu.grid(row=11, column=0, padx=20, pady=(10, 20))
        self.app_configurations_ftv = FtvAppsConfigurations().get_configurations()

        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.tabview.add("Application")
        self.tabview.add("Devices")
        self.tabview.add("RTU KPI")
        self.tabview.tab("Application").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Devices").grid_columnconfigure(0, weight=1)
        self.tabview.tab("RTU KPI").grid_columnconfigure(0, weight=1)

        ftv_app_names = FtvAppsConfigurations.get_ftv_app_names()
        self.optionmenu_ftv = customtkinter.CTkOptionMenu(self.tabview.tab("Application"), dynamic_resizing=True, values=ftv_app_names)
        self.optionmenu_ftv.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.selected_text_label = customtkinter.CTkLabel(self, text="", font=("Helvetica", 14))
        self.selected_text_label.grid(row=0, column=1, padx=20, pady=(10, 10))
        self.tabview.tab("Application").grid_columnconfigure(0, weight=1)
        self.optionmenu_ftvdevice = customtkinter.CTkOptionMenu(self.tabview.tab("Devices"), dynamic_resizing=True,
                                                                values=["Fire Tv Stick (Gen2)",
                                                                        "Fire Tv Stick 4k",
                                                                        "Fire Tv Stick Lite"])
        self.optionmenu_ftvdevice.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.tabview.tab("Devices").grid_columnconfigure(0, weight=1)

        self.optionmenu_rtu_kpi = customtkinter.CTkOptionMenu(self.tabview.tab("RTU KPI"), dynamic_resizing=True, values=["Cool_FF", "Warm_FF"])
        self.optionmenu_rtu_kpi.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.tabview.tab("RTU KPI").grid_columnconfigure(0, weight=1)

        self.selection_frame = customtkinter.CTkFrame(self)
        self.selection_frame.grid_configure(padx=10, pady=10)
        self.selection_frame.grid(row=1, column=1, padx=(20, 0), pady=(10, 20), sticky="nsew")
        self.log_text = Text(self.selection_frame, wrap='none', height=20, width=80, font=("Helvetica", 14))
        self.log_text.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="nsew")
        y_scrollbar = Scrollbar(self.selection_frame, command=self.log_text.yview)
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        self.log_text.config(yscrollcommand=y_scrollbar.set)
        x_scrollbar = Scrollbar(self.selection_frame, command=self.log_text.xview, orient='horizontal')
        x_scrollbar.grid(row=1, column=0, sticky='ew')
        self.log_text.config(xscrollcommand=x_scrollbar.set)
        self.selection_frame.columnconfigure(0, weight=1)
        self.selection_frame.rowconfigure(0, weight=1)

        self.selection_frame = customtkinter.CTkFrame(self)
        self.selection_frame.grid_configure(padx=10, pady=10)
        self.selection_frame.grid(row=1, column=2, padx=(20, 0), pady=(10, 20), sticky="nsew")

        self.appearance_mode_optionemenu.set("Light")
        self.scaling_optionmenu.set("100%")
        self.optionmenu_ftv.set("FTV Apps")
        self.optionmenu_ftvdevice.set("FTV Devices")
        self.optionmenu_rtu_kpi.set("RTU KPI")
        self.create_stopwatch_ui()

    def clear_logs(self):
        self.append_text_to_label("Button Clicked: Clear Logs")
        try:
            subprocess.Popen(["adb", "logcat", "-c"])
            print("Logs cleared successfully.")
            self.log_text.delete(1.0, END)
        except Exception as e:
            print(f"Error clearing logs: {e}")

    def start_logs(self):
        self.append_text_to_label("Button Clicked: Start Logs")
        if not self.log_capturing:
            self.log_capturing = True
            self.log_capture_thread = threading.Thread(target=self.capture_logs_thread)
            self.log_capture_thread.start()

    def capture_logs_thread(self):
        logcat_command = ["adb", "logcat", "-b", "all"]
        try:
            logcat_process = subprocess.Popen(logcat_command, stdout=subprocess.PIPE, text=True, shell=True)
            while self.log_capturing:
                line = logcat_process.stdout.readline()
                if not line:
                    break
                if "I ActivityManager: Fully drawn" in line:
                    self.log_text.insert(END, line)
            logcat_process.terminate()
        except Exception as e:
            print(f"Error capturing logs: {e}")

    def save_logs(self):
        self.append_text_to_label("Button Clicked: Save Logs")
        if self.log_capturing:
            try:
                logs_process = subprocess.run(["adb", "logcat", "-b", "all", "-d"], capture_output=True, text=True, shell=True)
                if logs_process.returncode == 0:
                    logs = logs_process.stdout
                    file_name = f"{self.optionmenu_ftv.get()}_{self.optionmenu_rtu_kpi.get()}_{self.optionmenu_ftvdevice.get()}.txt"
                    file_path = os.path.join(os.getcwd(), file_name)
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(logs)
                    print(f"Logs saved successfully to {file_path}")
                    self.log_capturing = False
                else:
                    print(f"Error capturing logs: {logs_process.stderr}")
            except Exception as e:
                print(f"Error saving logs: {e}")
        else:
            print("Please capture logs before saving.")

    def force_stop_app(self, ftv_force_stop_package):
        force_stop_command = f'adb shell am force-stop {ftv_force_stop_package}'
        subprocess.Popen(force_stop_command, shell=True)
        self.app_running = False

    def download_selected_apps(self):
        self.append_text_to_label("Button Clicked: Download")
        selected_ftv_app = self.optionmenu_ftv.get()
        for selected_app, app_params, app_param_key in [(selected_ftv_app, self.app_configurations_ftv, "ftv_app_name")]:
            if app := next((app for app in app_params if app[app_param_key] == selected_app), None):
                asin = app.get("asin")
                if not asin:
                    print(f"ASIN not found for {selected_app}. Please update the configuration.")
                    continue
                deep_link = f'amzn://apps/android?asin={asin}'
                try:
                    subprocess.Popen(f'adb shell am start -W -a android.intent.action.VIEW -d "{deep_link}"', shell=True)
                    print(f"{selected_app} downloaded successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Error downloading {selected_app} app: {e}")

    def uninstall_selected_app(self):
        self.append_text_to_label("Button Clicked: Uninstall")
        selected_ftv_app = self.optionmenu_ftv.get()
        if not selected_ftv_app:
            print("Please select an app to uninstall.")
            return
        for config in self.app_configurations_ftv:
            if selected_ftv_app == config["ftv_app_name"]:
                ftv_force_stop_package = config.get("ftv_force_stop_package")

                try:
                    subprocess.Popen(f'adb shell pm uninstall {ftv_force_stop_package}', shell=True)
                    print(f"{selected_ftv_app} uninstalled successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Error uninstalling {selected_ftv_app} app: {e}")

                break
        else:
            print("App not found or not selected.")

    def reset_to_defaults(self):
        if self.is_stopwatch_started:
            self.toggle_stopwatch_and_app()
        self.appearance_mode_optionemenu.set("Light")
        self.scaling_optionmenu.set("100%")
        self.optionmenu_ftv.set("FTV Apps")
        self.optionmenu_ftvdevice.set("FTV Devices")
        self.optionmenu_rtu_kpi.set("RTU KPI")
        self.change_appearance_mode_event("Light")
        self.change_scaling_event("100%")
        self.iteration_count = 0
        self.iteration_label.configure(text="No of Iterations: 0")
        self.iteration_times = []
        self.update_iteration_values_text()
        self.selected_text_label.configure(text="")

    def create_stopwatch_ui(self):
        tabview = customtkinter.CTkTabview(self, width=250)
        tabview.grid(row=0, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        tabview.add("Stopwatch")
        tabview.tab("Stopwatch").grid_columnconfigure(0, weight=1)

        launch_force_stop_button_text = "Launch"
        self.launch_force_stop_button= customtkinter.CTkButton(tabview.tab("Stopwatch"), text=launch_force_stop_button_text, command=self.toggle_stopwatch_and_app)
        self.launch_force_stop_button.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.time_label = customtkinter.CTkLabel(tabview.tab("Stopwatch"), text="00:000", font=("Helvetica", 24))
        self.time_label.grid(row=2, column=0, padx=20, pady=(10, 10))
        iteration_text = f"No of Iterations: {self.iteration_count}"
        self.iteration_label = customtkinter.CTkLabel(tabview.tab("Stopwatch"), text=iteration_text, font=("Helvetica", 16))
        self.iteration_label.grid(row=3, column=0, padx=20, pady=(10, 10))
        sort_button_text = "Sort Stopwatch Results"
        self.sort_button = customtkinter.CTkButton(tabview.tab("Stopwatch"), text=sort_button_text, command=self.sort_stopwatch_results)
        self.sort_button.grid(row=4, column=0, padx=20, pady=(10, 10))
        self.iteration_values_text = Text(self.selection_frame, wrap='none', height=20, width=30, font=("Helvetica", 14))
        self.iteration_values_text.grid(row=0, column=1, padx=20, pady=(10, 10), sticky="nsew")
        scrollbar = Scrollbar(self.selection_frame, command=self.iteration_values_text.yview)
        scrollbar.grid(row=0, column=2, sticky='nsew')
        self.iteration_values_text.config(yscrollcommand=scrollbar.set)
        self.selection_frame.columnconfigure(0, weight=1)
        self.selection_frame.rowconfigure(0, weight=1)

    def toggle_stopwatch_and_app(self):
        if self.is_stopwatch_started:
            self.is_stopwatch_started = False
            self.iteration_count += 1
            iteration_text = f"No of Iterations: {self.iteration_count}"
            self.iteration_label.configure(text=iteration_text)
            elapsed_time = time.time() - self.stopwatch_start_time
            self.iteration_times.append(elapsed_time)
            self.stopwatch_running = False
            self.stopwatch_start_time = 0
            self.time_label.configure(text="00:000")
            self.update_iteration_values_text()
            self.launch_force_stop_button.configure(text="Launch")
        else:
            self.is_stopwatch_started = True
            self.stopwatch_running = True
            self.stopwatch_start_time = time.time()
            self.update_stopwatch()
            if self.optionmenu_rtu_kpi.get() == "Warm_FF":
                self.launch_force_stop_button.configure(text="Push Background")
            else:
                self.launch_force_stop_button.configure(text="Force-Stop")
        self.manage_app("toggle")

    def update_iteration_values_text(self):
        self.iteration_values_text.delete(1.0, END)
        iteration_values_text = "\n".join(
            [f"Iteration : {i + 1} = {int(t)}.{int((t % 1) * 1000):03}" for i, t in enumerate(self.iteration_times)])
        self.iteration_values_text.insert(END, iteration_values_text)

    def update_stopwatch(self):
        if self.stopwatch_running:
            elapsed_time = time.time() - self.stopwatch_start_time
            self.update_time_label(elapsed_time)
            self.after(1, self.update_stopwatch)

    def update_time_label(self, elapsed_time):
        seconds = int(elapsed_time)
        milliseconds = int((elapsed_time - int(elapsed_time)) * 1000)
        time_str = f"{seconds:02}:{milliseconds:03}"
        self.time_label.configure(text=time_str)

    def sort_stopwatch_results(self):
        self.iteration_times.sort()
        self.update_iteration_values_text()

    def manage_app(self, action):
        ftv_app_name = self.optionmenu_ftv.get()
        rtu_kpi = self.optionmenu_rtu_kpi.get()
        ftv_device = self.optionmenu_ftvdevice.get()

        if not ftv_app_name or not rtu_kpi:
            print("Please select options in all required dropdowns.")
            return
        selected_text = f"Selected: {ftv_app_name}_{rtu_kpi}_{ftv_device}"

        for config in self.app_configurations_ftv:
            if (
                    ftv_app_name == config["ftv_app_name"]
                    and rtu_kpi in config["rtu_kpi"]
                    and (config["device_keyword"] in ftv_device)
            ):
                ftv_launch_package = config.get("ftv_launch_package")
                ftv_force_stop_package = config.get("ftv_force_stop_package")

                try:
                    if action == "toggle":
                        self.toggle_app_state(ftv_launch_package, ftv_force_stop_package, rtu_kpi)
                    elif action == "force_stop":
                        self.force_stop_app(ftv_force_stop_package)
                except subprocess.CalledProcessError as e:
                    print(f"Error managing {config['ftv_app_name']} app: {e}")
                break
        else:
            print("App not selected or RTU KPI is not Cool_FF/Warm_FF.")
        self.selected_text_label.configure(text=selected_text)

    def toggle_app_state(self, ftv_launch_package, ftv_force_stop_package, rtu_kpi):
        if self.app_running:
            command = "adb shell input keyevent 3" if rtu_kpi == "Warm_FF" else f'adb shell am force-stop {ftv_force_stop_package}'
        else:
            launch_command = f'adb shell am start -n {ftv_launch_package}'
            subprocess.Popen(launch_command, shell=True)
            self.app_running = True
            return
        subprocess.Popen(command, shell=True)
        self.app_running = not self.app_running

    def force_stop_app_button_click(self):
        self.manage_app("force_stop")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def append_text_to_label(self, text):
        current_text = self.selected_text_label.cget("text")
        if current_text:
            current_text += "\n" + text
        else:
            current_text = text
        self.selected_text_label.configure(text=current_text)


if __name__ == "__main__":
    app = App()
    app.mainloop()


