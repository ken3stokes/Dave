import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import os
import shutil
import threading
import schedule
import time
import json
import hashlib
from typing import List, Dict, Set
import mimetypes
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
import queue
import filecmp

class ScheduleWindow:
    def __init__(self, parent, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Schedule Backup")
        self.window.geometry("500x700")
        self.callback = callback
        
        # Schedule type
        type_frame = ttk.LabelFrame(self.window, text="Schedule Type")
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.schedule_type = tk.StringVar(value="recurring")
        ttk.Radiobutton(type_frame, text="Recurring", variable=self.schedule_type, 
                       value="recurring", command=self.toggle_schedule_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="One-time", variable=self.schedule_type, 
                       value="one-time", command=self.toggle_schedule_type).pack(side=tk.LEFT, padx=5)
        
        # Date selection
        date_frame = ttk.LabelFrame(self.window, text="Select Date")
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a frame for the date picker
        date_picker_frame = ttk.Frame(date_frame)
        date_picker_frame.pack(pady=10)
        
        self.date_picker = DateEntry(date_picker_frame, 
                                   width=12,
                                   year=datetime.now().year,
                                   month=datetime.now().month,
                                   day=datetime.now().day,
                                   selectmode='day',
                                   date_pattern='yyyy-mm-dd')
        self.date_picker.pack(expand=True)
        
        # Time selection
        time_frame = ttk.LabelFrame(self.window, text="Select Time")
        time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="00")
        self.ampm_var = tk.StringVar(value="PM")
        
        time_inner_frame = ttk.Frame(time_frame)
        time_inner_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_inner_frame, text="Hour:").pack(side=tk.LEFT, padx=5)
        hours = [str(i).zfill(2) for i in range(1, 13)]
        hour_combo = ttk.Combobox(time_inner_frame, textvariable=self.hour_var, 
                                values=hours, width=5)
        hour_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_inner_frame, text="Minute:").pack(side=tk.LEFT, padx=5)
        minutes = [str(i).zfill(2) for i in range(0, 60, 5)]
        minute_combo = ttk.Combobox(time_inner_frame, textvariable=self.minute_var, 
                                  values=minutes, width=5)
        minute_combo.pack(side=tk.LEFT, padx=5)
        
        ampm_combo = ttk.Combobox(time_inner_frame, textvariable=self.ampm_var, 
                                values=["AM", "PM"], width=5)
        ampm_combo.pack(side=tk.LEFT, padx=5)
        
        # Recurring options
        self.recurring_frame = ttk.LabelFrame(self.window, text="Recurring Options")
        self.recurring_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.recur_type = tk.StringVar(value="daily")
        ttk.Radiobutton(self.recurring_frame, text="Daily", 
                       variable=self.recur_type, value="daily").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.recurring_frame, text="Weekly", 
                       variable=self.recur_type, value="weekly").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.recurring_frame, text="Monthly", 
                       variable=self.recur_type, value="monthly").pack(side=tk.LEFT, padx=5)
        
        # Email notification
        email_frame = ttk.LabelFrame(self.window, text="Email Notification")
        email_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.notify_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(email_frame, text="Send email notification", 
                       variable=self.notify_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(email_frame, text="Email:").pack(side=tk.LEFT, padx=5)
        self.email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_var, 
                 width=30).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save Schedule", 
                  command=self.save_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Center the window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Make sure the window stays on top until closed
        self.window.transient(parent)
        self.window.grab_set()
    
    def toggle_schedule_type(self):
        if self.schedule_type.get() == "one-time":
            self.recurring_frame.pack_forget()
        else:
            self.recurring_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def get_schedule_time(self):
        hour = int(self.hour_var.get())
        if self.ampm_var.get() == "PM" and hour != 12:
            hour += 12
        elif self.ampm_var.get() == "AM" and hour == 12:
            hour = 0
            
        minute = int(self.minute_var.get())
        date = self.date_picker.get_date()
        
        return datetime(date.year, date.month, date.day, hour, minute)
    
    def save_schedule(self):
        schedule_time = self.get_schedule_time()
        schedule_info = {
            "type": self.schedule_type.get(),
            "time": schedule_time.strftime("%Y-%m-%d %H:%M"),
            "recur_type": self.recur_type.get() if self.schedule_type.get() == "recurring" else None,
            "notify": self.notify_var.get(),
            "email": self.email_var.get() if self.notify_var.get() else None
        }
        
        self.callback(schedule_info)
        self.window.destroy()

class EmailSettingsWindow:
    def __init__(self, parent, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Email Settings")
        self.window.geometry("500x400")
        self.callback = callback
        
        style = ttk.Style()
        style.configure('Settings.TLabelframe', padding=10)
        style.configure('Settings.TLabelframe.Label', font=('Helvetica', 10, 'bold'))
        
        # Create main container with padding
        main_container = ttk.Frame(self.window, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Server Settings group
        server_frame = ttk.LabelFrame(main_container, text="Server Settings", 
                                    style='Settings.TLabelframe')
        server_frame.pack(fill=tk.X, pady=(0, 15))
        
        # SMTP Server with dropdown
        server_container = ttk.Frame(server_frame)
        server_container.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(server_container, text="SMTP Server:").pack(anchor=tk.W, pady=(0, 5))
        
        server_input_frame = ttk.Frame(server_container)
        server_input_frame.pack(fill=tk.X)
        
        self.server_var = tk.StringVar()
        self.server_entry = ttk.Entry(server_input_frame, textvariable=self.server_var)
        self.server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Common servers dropdown
        self.common_servers = {
            "Select provider...": "",
            "Gmail": "smtp.gmail.com",
            "Outlook/Office 365": "smtp.office365.com",
            "ProtonMail": "smtp.protonmail.ch"
        }
        
        server_combo = ttk.Combobox(server_input_frame, 
                                  values=list(self.common_servers.keys()), 
                                  width=20)
        server_combo.pack(side=tk.LEFT, padx=(10, 0))
        server_combo.set("Select provider...")
        server_combo.bind('<<ComboboxSelected>>', 
                        lambda e: self.server_var.set(self.common_servers[server_combo.get()]))
        
        # Port
        port_container = ttk.Frame(server_frame)
        port_container.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(port_container, text="Port:").pack(anchor=tk.W, pady=(0, 5))
        
        port_input_frame = ttk.Frame(port_container)
        port_input_frame.pack(fill=tk.X)
        
        self.port_var = tk.StringVar(value="587")
        ttk.Entry(port_input_frame, textvariable=self.port_var, 
                 width=10).pack(side=tk.LEFT)
        ttk.Label(port_input_frame, 
                 text="(Usually 587 for TLS)").pack(side=tk.LEFT, padx=(10, 0))
        
        # Authentication Settings group
        auth_frame = ttk.LabelFrame(main_container, text="Authentication", 
                                  style='Settings.TLabelframe')
        auth_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Email
        email_container = ttk.Frame(auth_frame)
        email_container.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(email_container, text="Email Address:").pack(anchor=tk.W, pady=(0, 5))
        self.email_var = tk.StringVar()
        ttk.Entry(email_container, textvariable=self.email_var).pack(fill=tk.X)
        
        # Password
        password_container = ttk.Frame(auth_frame)
        password_container.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(password_container, text="Password:").pack(anchor=tk.W, pady=(0, 5))
        self.password_var = tk.StringVar()
        ttk.Entry(password_container, textvariable=self.password_var, 
                 show="*").pack(fill=tk.X)
        
        # Buttons frame
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Test connection button
        ttk.Button(button_frame, text="Test Connection", 
                  command=self.test_connection, width=20).pack(side=tk.LEFT, padx=5)
        
        # Save button
        ttk.Button(button_frame, text="Save Settings", 
                  command=self.save_settings, width=20).pack(side=tk.RIGHT, padx=5)
        
        # Load existing settings if any
        self.load_settings()
        
        # Center the window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        self.window.transient(parent)
        self.window.grab_set()
    
    def load_settings(self):
        try:
            if os.path.exists('email_settings.json'):
                with open('email_settings.json', 'r') as f:
                    settings = json.load(f)
                    self.server_var.set(settings.get('smtp_server', ''))
                    self.port_var.set(settings.get('smtp_port', '587'))
                    self.email_var.set(settings.get('email_address', ''))
                    # Don't load password for security
        except Exception as e:
            print(f"Error loading email settings: {e}")
    
    def save_settings(self):
        settings = {
            'smtp_server': self.server_var.get(),
            'smtp_port': self.port_var.get(),
            'email_address': self.email_var.get(),
            'email_password': self.password_var.get()
        }
        
        # Validate settings
        if not all(settings.values()):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        try:
            # Save settings
            with open('email_settings.json', 'w') as f:
                json.dump(settings, f)
            
            # Call callback with new settings
            self.callback(settings)
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def test_connection(self):
        settings = {
            'smtp_server': self.server_var.get(),
            'smtp_port': self.port_var.get(),
            'email_address': self.email_var.get(),
            'email_password': self.password_var.get()
        }
        
        # Validate settings
        if not all(settings.values()):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        try:
            # Test SMTP connection
            with smtplib.SMTP(settings['smtp_server'], int(settings['smtp_port'])) as server:
                server.starttls()
                server.login(settings['email_address'], settings['email_password'])
            
            messagebox.showinfo("Success", "Connection test successful!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Connection test failed: {e}")

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Backup Application")
        self.root.geometry("1000x600")
        
        # Default directories and scheduling
        self.source_files = []
        self.dest_dir = os.path.join(os.path.expanduser("~"), "FileBackups")
        self.config_file = "backup_config.json"
        self.schedule_queue = queue.Queue()
        self.scheduler_running = False
        self.scheduled_backups = []
        self.email_settings = None
        self.load_email_settings()
        
        # Initialize variables
        self.source_files = set()
        self.schedule_thread = None
        self.file_filters = set()
        self.current_filter = "All Files"
        self.operation_mode = tk.StringVar(value="copy")
        
        self.load_config()
        
        if not os.path.exists(self.dest_dir):
            os.makedirs(self.dest_dir)
        
        self.create_widgets()
        self.setup_schedules()
        self.start_scheduler()
        
        # Right-click menu
        self.create_context_menu()
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Remove from List", command=self.remove_selected)
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
        self.context_menu.add_command(label="File Info", command=self.show_file_info)
        
        self.file_listbox.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        try:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.file_listbox.nearest(event.y))
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def remove_selected(self):
        selection = self.file_listbox.curselection()
        if selection:
            self.source_files.pop(selection[0])
            self.file_listbox.delete(selection[0])
            self.update_files_label()
    
    def show_in_explorer(self):
        selection = self.file_listbox.curselection()
        if selection:
            file_path = self.source_files[selection[0]]
            os.system(f'explorer /select,"{file_path}"')
    
    def show_file_info(self):
        selection = self.file_listbox.curselection()
        if selection:
            file_path = self.source_files[selection[0]]
            stats = os.stat(file_path)
            info = f"File: {os.path.basename(file_path)}\n"
            info += f"Size: {self.format_size(stats.st_size)}\n"
            info += f"Modified: {datetime.fromtimestamp(stats.st_mtime)}\n"
            info += f"Type: {mimetypes.guess_type(file_path)[0] or 'Unknown'}"
            messagebox.showinfo("File Information", info)
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def create_widgets(self):
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side (Source)
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Source Files Frame
        source_frame = ttk.LabelFrame(left_frame, text="Source Files")
        source_frame.pack(fill=tk.BOTH, expand=True)
        
        # File type filter
        filter_frame = ttk.Frame(source_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="All Files")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                  values=["All Files", "Documents", "Images", "Videos", "Custom..."])
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.apply_filter)
        
        # Source controls
        source_controls = ttk.Frame(source_frame)
        source_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(source_controls, text="Select Files", 
                  command=self.select_files).pack(side=tk.LEFT, padx=5)
        ttk.Label(source_controls, text="Selected:").pack(side=tk.LEFT, padx=5)
        self.files_label = ttk.Label(source_controls, text="0 files")
        self.files_label.pack(side=tk.LEFT, padx=5)
        
        # Operation mode
        op_frame = ttk.Frame(source_frame)
        op_frame.pack(fill=tk.X, pady=5)
        ttk.Label(op_frame, text="Operation:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(op_frame, text="Copy", variable=self.operation_mode, 
                       value="copy").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(op_frame, text="Move", variable=self.operation_mode, 
                       value="move").pack(side=tk.LEFT, padx=5)
        
        # Source list
        source_list_frame = ttk.Frame(source_frame)
        source_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        source_scrollbar = ttk.Scrollbar(source_list_frame)
        source_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(source_list_frame, 
                                     yscrollcommand=source_scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        source_scrollbar.config(command=self.file_listbox.yview)
        
        # Right side (Destination)
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Destination Frame
        dest_frame = ttk.LabelFrame(right_frame, text="Destination Directory")
        dest_frame.pack(fill=tk.BOTH, expand=True)
        
        # Destination controls
        dest_controls = ttk.Frame(dest_frame)
        dest_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(dest_controls, text="Change Destination", 
                  command=self.change_dest_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(dest_controls, text="Compare Files", 
                  command=self.compare_files).pack(side=tk.LEFT, padx=5)
        
        # Destination path
        dest_path_frame = ttk.Frame(dest_frame)
        dest_path_frame.pack(fill=tk.X, pady=5)
        
        self.dest_label = ttk.Label(dest_path_frame, text=self.dest_dir, 
                                  wraplength=400)
        self.dest_label.pack(fill=tk.X, padx=5)
        
        # Destination preview
        dest_preview_frame = ttk.Frame(dest_frame)
        dest_preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        dest_scrollbar = ttk.Scrollbar(dest_preview_frame)
        dest_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dest_listbox = tk.Listbox(dest_preview_frame, 
                                     yscrollcommand=dest_scrollbar.set)
        self.dest_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dest_scrollbar.config(command=self.dest_listbox.yview)
        
        # Progress Frame
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, 
                                          variable=self.progress_var,
                                          maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(pady=2)
        
        # Bottom Frame
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Schedule Frame
        schedule_frame = ttk.LabelFrame(bottom_frame, text="Backup Schedule")
        schedule_frame.pack(fill=tk.X, pady=5)
        
        schedule_buttons = ttk.Frame(schedule_frame)
        schedule_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(schedule_buttons, text="Add Schedule", 
                  command=self.show_schedule_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(schedule_buttons, text="View Schedules", 
                  command=self.show_schedules).pack(side=tk.LEFT, padx=5)
        
        self.schedule_status = tk.StringVar(value="Active Schedules: 0")
        ttk.Label(schedule_buttons, textvariable=self.schedule_status).pack(
            side=tk.LEFT, padx=20)
        
        # Action Buttons
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Start Backup Now", 
                  command=self.start_backup, style='success.TButton',
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear List", 
                  command=self.clear_list, width=15).pack(side=tk.LEFT, padx=5)
        
        # Add Settings button to the menu
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Email Settings", 
                                command=self.show_email_settings)
        
        self.update_destination_preview()
    
    def apply_filter(self, event=None):
        filter_type = self.filter_var.get()
        if filter_type == "Custom...":
            custom_filter = tk.simpledialog.askstring(
                "Custom Filter", 
                "Enter file extensions (comma-separated, e.g., .txt,.pdf):")
            if custom_filter:
                self.file_filters = set(ext.strip().lower() for ext in custom_filter.split(','))
            else:
                self.filter_var.set("All Files")
                return
        elif filter_type == "Documents":
            self.file_filters = {'.doc', '.docx', '.pdf', '.txt', '.rtf', '.odt'}
        elif filter_type == "Images":
            self.file_filters = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        elif filter_type == "Videos":
            self.file_filters = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'}
        else:  # All Files
            self.file_filters = set()
        
        self.refresh_file_list()
    
    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for file in self.source_files:
            if self.matches_filter(file):
                self.file_listbox.insert(tk.END, file)
        self.update_files_label()
    
    def matches_filter(self, file_path):
        if not self.file_filters:
            return True
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.file_filters
    
    def compare_files(self):
        if not self.file_listbox.get(0, tk.END):
            messagebox.showwarning("Warning", "No files selected to compare!")
            return
        
        comparison = []
        for file in self.file_listbox.get(0, tk.END):
            src_file = file
            dest_file = os.path.join(self.dest_dir, os.path.basename(file))
            
            if not os.path.exists(dest_file):
                status = "New file"
            elif filecmp.cmp(src_file, dest_file, shallow=False):
                status = "Identical"
            else:
                status = "Different"
            
            comparison.append(f"{os.path.basename(file)}: {status}")
        
        # Show comparison results
        comparison_window = tk.Toplevel(self.root)
        comparison_window.title("File Comparison Results")
        comparison_window.geometry("400x300")
        
        result_text = tk.Text(comparison_window, wrap=tk.WORD)
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for line in comparison:
            result_text.insert(tk.END, line + "\n")
        result_text.config(state=tk.DISABLED)
    
    def verify_backup(self, source_file: str, dest_file: str) -> bool:
        """Verify backup using SHA-256 hash comparison"""
        def calculate_hash(filename: str) -> str:
            sha256_hash = hashlib.sha256()
            with open(filename, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        
        try:
            return calculate_hash(source_file) == calculate_hash(dest_file)
        except Exception:
            return False
    
    def start_backup(self):
        if not self.file_listbox.get(0, tk.END):
            messagebox.showwarning("Warning", "Please select files to backup first!")
            return
        
        try:
            files_to_process = [f for f in self.file_listbox.get(0, tk.END)]
            total_files = len(files_to_process)
            processed_files = 0
            
            self.progress_var.set(0)
            self.progress_label.config(text="Starting backup...")
            
            for file in files_to_process:
                filename = os.path.basename(file)
                destination = os.path.join(self.dest_dir, filename)
                
                # If file exists, add a number to the filename
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(destination):
                    destination = os.path.join(self.dest_dir, f"{base}_{counter}{ext}")
                    counter += 1
                
                # Perform the operation (copy or move)
                if self.operation_mode.get() == "copy":
                    shutil.copy2(file, destination)
                else:  # move
                    shutil.move(file, destination)
                
                # Verify the backup
                if not self.verify_backup(file, destination):
                    raise Exception(f"Verification failed for {filename}")
                
                processed_files += 1
                progress = (processed_files / total_files) * 100
                self.progress_var.set(progress)
                self.progress_label.config(
                    text=f"Processing: {processed_files}/{total_files} - {filename}")
                self.root.update()
            
            self.update_destination_preview()
            self.progress_label.config(text="Backup completed successfully!")
            
            if self.operation_mode.get() == "move":
                self.clear_list()
            
            messagebox.showinfo("Success", 
                              f"Backup completed successfully!\n{processed_files} files processed")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during backup:\n{str(e)}")
        finally:
            self.progress_var.set(0)
            self.progress_label.config(text="")
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.dest_dir = config.get('dest_dir', self.dest_dir)
                    self.scheduled_backups = config.get('schedules', [])
                    
                    # Convert stored times back to datetime objects
                    for schedule in self.scheduled_backups:
                        schedule['time'] = parse(schedule['time'])
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        try:
            schedules = []
            for schedule in self.scheduled_backups:
                schedule_copy = schedule.copy()
                schedule_copy['time'] = schedule_copy['time'].strftime("%Y-%m-%d %H:%M")
                schedules.append(schedule_copy)
            
            with open(self.config_file, 'w') as f:
                json.dump({
                    'dest_dir': self.dest_dir,
                    'schedules': schedules
                }, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def change_dest_dir(self):
        new_dir = filedialog.askdirectory(initialdir=self.dest_dir)
        if new_dir:
            self.dest_dir = new_dir
            self.dest_label.config(text=self.dest_dir)
            self.save_config()
            self.update_destination_preview()
    
    def select_files(self):
        files = filedialog.askopenfilenames()
        for file in files:
            if file not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, file)
                self.source_files.append(file)
        
        self.update_files_label()
    
    def update_files_label(self):
        count = len(self.file_listbox.get(0, tk.END))
        self.files_label.config(text=f"{count} files")
    
    def clear_list(self):
        self.file_listbox.delete(0, tk.END)
        self.source_files = []
        self.update_files_label()
        if self.scheduler_running:
            self.stop_scheduler()
    
    def update_destination_preview(self):
        """Update the destination preview with existing backups"""
        self.dest_listbox.delete(0, tk.END)
        if os.path.exists(self.dest_dir):
            for item in sorted(os.listdir(self.dest_dir), reverse=True):
                self.dest_listbox.insert(tk.END, item)
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        if not self.scheduler_running:
            self.scheduler_running = True
            self.schedule_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.schedule_thread.start()
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(1)  # Check every second
    
    def stop_scheduler(self):
        """Stop the scheduler thread"""
        self.scheduler_running = False
        if self.schedule_thread:
            self.schedule_thread.join(timeout=1)
    
    def setup_schedules(self):
        """Set up all scheduled backups"""
        schedule.clear()
        
        for backup_schedule in self.scheduled_backups:
            schedule_time = parse(backup_schedule['time']) if isinstance(backup_schedule['time'], str) else backup_schedule['time']
            
            if backup_schedule['type'] == "one-time":
                if schedule_time > datetime.now():
                    # For one-time schedules, schedule it only if it's in the future
                    job = schedule.every().day.at(schedule_time.strftime("%H:%M")).do(
                        self.run_scheduled_backup, backup_schedule
                    ).tag(f"one-time_{schedule_time.strftime('%Y%m%d%H%M')}")
            else:
                # For recurring schedules
                if backup_schedule['recur_type'] == "daily":
                    job = schedule.every().day.at(schedule_time.strftime("%H:%M")).do(
                        self.run_scheduled_backup, backup_schedule
                    )
                elif backup_schedule['recur_type'] == "weekly":
                    # Schedule for the same day of week
                    job = schedule.every().week.at(schedule_time.strftime("%H:%M")).do(
                        self.run_scheduled_backup, backup_schedule
                    )
                elif backup_schedule['recur_type'] == "monthly":
                    # Schedule for the same day of month
                    day = schedule_time.day
                    job = schedule.every().month.at(schedule_time.strftime("%H:%M")).do(
                        self.run_scheduled_backup, backup_schedule
                    )
    
    def run_scheduled_backup(self, schedule_info):
        """Run a scheduled backup"""
        try:
            print(f"Running scheduled backup at {datetime.now()}")
            self.start_backup()
            
            if schedule_info.get('notify') and schedule_info.get('email'):
                self.send_notification(schedule_info['email'])
            
            if schedule_info['type'] == "one-time":
                # Remove one-time schedules after they run
                self.scheduled_backups = [s for s in self.scheduled_backups 
                                        if s != schedule_info]
                self.save_config()
                self.update_schedule_status()
                
            return schedule.CancelJob if schedule_info['type'] == "one-time" else None
            
        except Exception as e:
            print(f"Error in scheduled backup: {e}")
            messagebox.showerror("Scheduled Backup Error", 
                               f"Failed to run scheduled backup: {e}")
            return None
    
    def add_schedule(self, schedule_info):
        """Add a new backup schedule"""
        self.scheduled_backups.append(schedule_info)
        self.save_config()
        self.update_schedule_status()
        self.setup_schedules()  # Refresh all schedules
    
    def show_schedule_window(self):
        if not self.file_listbox.get(0, tk.END):
            messagebox.showwarning("Warning", "Please select files to backup first!")
            return
        
        ScheduleWindow(self.root, self.add_schedule)
    
    def show_schedules(self):
        if not self.scheduled_backups:
            messagebox.showinfo("Schedules", "No scheduled backups.")
            return
        
        schedule_window = tk.Toplevel(self.root)
        schedule_window.title("Scheduled Backups")
        schedule_window.geometry("400x300")
        
        # Create treeview
        columns = ("Type", "Date", "Time", "Recurrence", "Email")
        tree = ttk.Treeview(schedule_window, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=75)
        
        for schedule in self.scheduled_backups:
            schedule_time = parse(schedule['time']) if isinstance(schedule['time'], str) else schedule['time']
            values = (
                schedule['type'],
                schedule_time.strftime("%Y-%m-%d"),
                schedule_time.strftime("%I:%M %p"),
                schedule.get('recur_type', 'N/A'),
                "Yes" if schedule.get('notify') else "No"
            )
            tree.insert("", "end", values=values)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def remove_schedule():
            selection = tree.selection()
            if selection:
                idx = tree.index(selection[0])
                self.scheduled_backups.pop(idx)
                self.save_config()
                self.setup_schedules()
                self.update_schedule_status()
                tree.delete(selection[0])
        
        ttk.Button(schedule_window, text="Remove Selected", 
                  command=remove_schedule).pack(pady=5)
    
    def update_schedule_status(self):
        active_count = len([s for s in self.scheduled_backups 
                          if s['type'] == "recurring" or 
                          parse(s['time']) > datetime.now()])
        self.schedule_status.set(f"Active Schedules: {active_count}")
    
    def load_email_settings(self):
        try:
            if os.path.exists('email_settings.json'):
                with open('email_settings.json', 'r') as f:
                    self.email_settings = json.load(f)
        except Exception as e:
            print(f"Error loading email settings: {e}")
    
    def update_email_settings(self, settings):
        self.email_settings = settings
    
    def show_email_settings(self):
        EmailSettingsWindow(self.root, self.update_email_settings)
    
    def send_notification(self, recipient_email):
        if not self.email_settings:
            messagebox.showerror("Email Error", 
                               "Please configure email settings first!")
            self.show_email_settings()
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_settings['email_address']
            msg['To'] = recipient_email
            msg['Subject'] = "Backup Completed"
            
            body = f"""
            Backup completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M')}
            Destination: {self.dest_dir}
            
            Files backed up:
            {chr(10).join('- ' + os.path.basename(f) for f in self.source_files)}
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.email_settings['smtp_server'], 
                            int(self.email_settings['smtp_port'])) as server:
                server.starttls()
                server.login(self.email_settings['email_address'], 
                           self.email_settings['email_password'])
                server.send_message(msg)
            
            print(f"Email notification sent to {recipient_email}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to send email notification: {error_msg}")
            messagebox.showerror("Email Error", 
                               f"Failed to send email notification: {error_msg}\n\n"
                               "Please check your email settings and internet connection.")    
    
    def __del__(self):
        """Clean up when the application closes"""
        self.stop_scheduler()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("File Backup Application")
    app = BackupApp(root)
    root.mainloop()
