import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import threading
import subprocess
import os

def finde_movies_path():
    parent_dir = os.path.join(os.environ['USERPROFILE'], 'Movies')
    dir = os.path.join(parent_dir, 'StreamPirate')
    os.makedirs(dir, exist_ok=True)
    return dir

# Function to check for NPM and install it if missing
def setup_environment():
    def env_npm():
        # Set NPM prefix to a specific directory
        new_npm_path = os.path.join(os.environ['USERPROFILE'], 'npm')
        subprocess.run(f"npm config set prefix '{new_npm_path}'", shell=True)
        
        # Use 'setx' to add the new NPM directory to the system PATH permanently
        # Note: 'setx' can handle a maximum of 1024 characters for the PATH. 
        # This operation might truncate the PATH if it's already close to this limit.
        current_path = os.environ.get('PATH', '')
        if new_npm_path not in current_path:
            subprocess.run(f"setx PATH \"%PATH%;{new_npm_path}\\bin\"", shell=True)
            
        return find_npm()

    def find_npm():
        return subprocess.call("npm --version", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

    def install_npm():
        if env_npm():
            return True
        install_cmd = "Start-Process -Wait -FilePath powershell -ArgumentList \"& {Invoke-WebRequest -Uri https://nodejs.org/dist/latest/win-x64/node.exe -OutFile $env:TEMP\\node.exe; Start-Process -Wait -FilePath $env:TEMP\\node.exe -ArgumentList '/verysilent /msicl'}\""
        subprocess.call(install_cmd, shell=True)
        if not find_npm():
            messagebox.showerror("Error", "Failed to install npm. Please install it manually from https://nodejs.org.")
            exit()

    def find_webtorrent():
        return subprocess.call("webtorrent --version", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

    def install_webtorrent():
        if not find_npm():
            
            install_npm()
        subprocess.call("npm install -g webtorrent-cli", shell=True)
        if not find_webtorrent():
            messagebox.showerror("Error", "Failed to install WebTorrent. Please install it manually using 'npm install -g webtorrent-cli'.")
            exit()

    install_webtorrent()

# Function to find VLC path
def find_vlc():
    possible_paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'VideoLAN', 'VLC', 'vlc.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'VideoLAN', 'VLC', 'vlc.exe'),
    ] if os.name == 'nt' else ['/usr/bin/vlc', '/usr/local/bin/vlc']

    for path in possible_paths:
        if os.path.exists(path) or subprocess.call(f"which {path}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return path

    messagebox.showerror("Error", "VLC Media Player is required but was not found. Please install VLC.")
    exit()


# Function to update GUI with messages
def update_status(message):
    
    status_box.config(state=tk.NORMAL)
    status_box.insert(tk.END, message + "\n")
    status_box.yview(tk.END)
    status_box.config(state=tk.DISABLED)

# Function to stream content using WebTorrent and VLC
def stream_content(content_path, subtitles_path=None):
    vlc_path = find_vlc()
    if not vlc_path:
        update_status("Error: VLC not found. Please install VLC and try again.")
        return
    movies_path = finde_movies_path()
    cmd = f'webtorrent "{content_path}" --vlc --out {movies_path}'
    if subtitles_path:
        cmd += f' --subtitles "{subtitles_path}"'
    update_status("Starting stream...")

    def run_command():
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
        for line in process.stdout:
            update_status(line.strip())
        process.wait()

    threading.Thread(target=run_command).start()

# GUI setup


root = tk.Tk()
root.title("StreamPirate: Torrent Streamer")
root.geometry("600x400")

# Torrent input field and button
magnet_label = tk.Label(root, text="Magnet Link or .Torrent File:")
magnet_label.pack(pady=(10,0))
magnet_entry = tk.Entry(root, width=50)
magnet_entry.pack(pady=(0,10))
magnet_button = tk.Button(root, text="Add Torrent", 
                          command=lambda: magnet_entry.insert(tk.END, filedialog.askopenfilename(filetypes=[("Torrent Files", "*.torrent")])), 
                          bg="#0000FF", fg="white", bd=0, padx=20, pady=5)
magnet_button.pack(pady=(0,10))

# Subtitles input field and button
subtitles_label = tk.Label(root, text="Subtitles File (optional):")
subtitles_label.pack()
subtitles_entry = tk.Entry(root, width=50)
subtitles_entry.pack(pady=(0,10))
subtitles_button = tk.Button(root, text="Add Subtitles", 
                             command=lambda: subtitles_entry.insert(tk.END, filedialog.askopenfilename(filetypes=[("Subtitles Files", "*.srt")])), 
                             bg="#FFA500", fg="white", bd=0, padx=20, pady=5)
subtitles_button.pack(pady=(0,10))

# Stream button
stream_button = tk.Button(root, text="Stream", 
                          command=lambda: stream_content(magnet_entry.get(), subtitles_entry.get()), 
                          bg="#00FF00", fg="white", bd=0, padx=20, pady=5)
stream_button.pack(pady=(0,20))

# Status box
status_box = scrolledtext.ScrolledText(root, height=10)
status_box.pack(expand=True, fill=tk.BOTH)
status_box.config(state=tk.DISABLED)

# Check and install environment on start
threading.Thread(target=setup_environment, daemon=True).start()

root.mainloop()