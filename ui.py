import socket
import sys
import threading
import time
import tkinter as tk
import tkinter.filedialog as filedialog
from datetime import datetime
from tkinter import colorchooser, font, messagebox, scrolledtext, ttk

from picture_encryption_socket import PictureEncryptionSocket

ENCODING = 'utf-16'


class ChatClient:
    def __init__(self, master):
        self.is_saving_enabled = True  # Initially, saving is disabled
        self.bg_color = None
        self.username = None
        self.master = master
        self.user_socket = None
        self.receive_thread = None
        self.is_connected = False
        self.stop_thread = False

        self.theme = "light"  # Default theme
        self.send_color_light = "#c8e6c9"
        self.receive_color_light = "#e1f5fe"
        self.send_color_dark = "#4caf50"
        self.receive_color_dark = "#7e57c2"
        self.bg_light = "#ffffff"
        self.bg_dark = "#2b2b2b"
        self.text_light = "#000000"
        self.text_dark = "#ffffff"

        self.send_color = self.send_color_light
        self.receive_color = self.receive_color_light
        self.font_family = "Segue UI"
        self.font_size = 11

        def custom_askstring_and_colors():
            dialog = tk.Toplevel(master)
            dialog.title("Chat Configuration")
            dialog.geometry("700x400")
            dialog.grab_set()

            tk.Label(dialog, text="Select IP address of the other user:", font=("Arial", 14)).pack(pady=10)

            ip_var = tk.StringVar()
            ip_choices = ["127.0.0.1", "192.168.1.92"]
            ip_dropdown_frame = tk.Frame(dialog)
            ip_dropdown_frame.pack()

            ip_dropdown = ttk.Combobox(
                ip_dropdown_frame,
                textvariable=ip_var,
                values=ip_choices,
                font=("Arial", 13),
                width=47,
                state="readonly",
            )
            ip_dropdown.pack(side=tk.LEFT, padx=(0, 5))
            ip_dropdown.set(ip_choices[0])  # Set default selection

            tk.Label(dialog, text="Enter your username:", font=("Arial", 14)).pack(pady=10)
            username_var = tk.StringVar()
            tk.Entry(dialog, textvariable=username_var, font=("Arial", 13), width=50).pack()

            color_frame = tk.Frame(dialog)
            color_frame.pack(pady=20)

            tk.Label(color_frame, text="Bubble Colors:", font=("Arial", 13)).grid(row=0, columnspan=2, pady=5)

            def choose_send_color():
                color = colorchooser.askcolor(title="Choose Sent Message Color")[1]
                if color:
                    self.send_color = color
                    send_color_btn.config(bg=color)

            def choose_receive_color():
                color = colorchooser.askcolor(title="Choose Received Message Color")[1]
                if color:
                    self.receive_color = color
                    receive_color_btn.config(bg=color)

            send_color_btn = tk.Button(color_frame, text="Sent Message Color", command=choose_send_color, width=25)
            send_color_btn.grid(row=1, column=0, padx=10)

            receive_color_btn = tk.Button(
                color_frame, text="Received Message Color", command=choose_receive_color, width=25
            )
            receive_color_btn.grid(row=1, column=1, padx=10)

            def on_ok():
                dialog.result = (ip_var.get(), username_var.get())
                dialog.destroy()

            def on_cancel():
                dialog.result = None
                dialog.destroy()

            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=20)
            tk.Button(btn_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.RIGHT, padx=10)

            master.wait_window(dialog)
            return dialog.result

        self.master.withdraw()

        result = custom_askstring_and_colors()
        if not result:
            master.destroy()
            sys.exit("Startup cancelled.")

        self.host, self.username = result
        if not self.username:
            self.username = f"User_{int(time.time()) % 10000}"
            messagebox.showwarning("Username", f"No username entered. Using default: {self.username}", parent=master)

        self.master.deiconify()
        master.title(f"Chat user - {self.username}")
        master.geometry("700x600")

        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.toolbar = tk.Frame(self.main_frame, bg="#f7f7f7")
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)

        self.color_button = tk.Button(self.toolbar, text="🎨 Bubble Colors", command=self.open_color_chooser)
        self.color_button.pack(side=tk.LEFT, padx=5)

        self.font_button = tk.Button(self.toolbar, text="🔤 Font Type", command=self.choose_font_family)
        self.font_button.pack(side=tk.LEFT, padx=5)

        self.size_button = tk.Button(self.toolbar, text="🔠 Font Size", command=self.choose_font_size)
        self.size_button.pack(side=tk.LEFT, padx=5)

        self.bg_color_button = tk.Button(self.toolbar, text="🎨 Chat Background", command=self.choose_bg_color)
        self.bg_color_button.pack(side=tk.LEFT, padx=5)

        self.theme_button = tk.Button(self.toolbar, text="🌓 Toggle Theme", command=self.toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.toolbar, text="💲 Save Chat", command=self.save_chat_to_file)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.status_frame = tk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X)
        self.status_label = tk.Label(self.status_frame, text="Status: Disconnected", fg="red")
        self.status_label.pack(anchor='w', padx=10)

        self.message_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.message_area.pack(padx=10, pady=(5, 0), expand=True, fill=tk.BOTH)
        self.message_area.configure(font=(self.font_family, self.font_size), padx=10, pady=10)

        self.message_area.tag_configure(
            "left_bubble",
            justify="left",
            lmargin1=10,
            lmargin2=10,
            background=self.receive_color,
            spacing1=5,
            spacing3=5,
            wrap='word',
        )
        self.message_area.tag_configure(
            "right_bubble", justify="right", rmargin=10, background=self.send_color, spacing1=5, spacing3=5, wrap='word'
        )

        self.input_frame = tk.Frame(self.main_frame)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X)

        self.message_entry = tk.Entry(self.input_frame, font=(self.font_family, 14))
        self.message_entry.bind("<Return>", self.send_message_event)
        self.message_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message_event)
        self.send_button.pack(side=tk.RIGHT)

        self.message_entry.focus_set()
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.connect_to_server()

    def save_chat_to_file(self):
        print("Save chat method triggered.")  # Debugging line

        # Ask the user for a filename and location (using a file dialog)
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            initialfile=f"Chat_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt",  # Default name with timestamp
            title="Save Chat As",
        )

        # If the user cancels the dialog (filename is an empty string), use the default timestamp name
        if not filename:
            # Use the default filename
            filename = f"Chat_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

        try:
            content = self.message_area.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("No Content", "There are no messages to save.", parent=self.master)
                return

            with open(filename, "w", encoding=ENCODING) as f:
                f.write(content)
            messagebox.showinfo("Chat Saved", f"Chat saved to {filename}", parent=self.master)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save chat:\n{e}", parent=self.master)

    def choose_bg_color(self):
        color = colorchooser.askcolor(title="Choose Chat Background Color")[1]
        if color:
            self.bg_color = color
            self.update_chat_bg_color()  # This updates the chat background to the new color

    def update_chat_bg_color(self):
        # Update the background color of various components to reflect the new color
        self.master.configure(bg=self.bg_color)
        self.main_frame.configure(bg=self.bg_color)
        self.toolbar.configure(bg=self.bg_color)
        self.status_frame.configure(bg=self.bg_color)
        self.status_label.configure(bg=self.bg_color)
        self.message_area.configure(bg=self.bg_color)
        self.input_frame.configure(bg=self.bg_color)
        self.message_entry.configure(bg=self.bg_color)

    def choose_font_family(self):
        families = list(font.families())
        top = tk.Toplevel(self.master)
        top.title("Choose Font Family")
        listbox = tk.Listbox(top, width=50, height=20)
        listbox.pack(padx=10, pady=10)
        for fam in sorted(families):
            listbox.insert(tk.END, fam)

        def apply():
            selected = listbox.get(tk.ACTIVE)
            if selected:
                self.font_family = selected
                self.message_area.configure(font=(self.font_family, self.font_size))
                self.message_entry.configure(font=(self.font_family, 14))
            top.destroy()

        tk.Button(top, text="Apply", command=apply).pack(pady=5)

    def choose_font_size(self):
        top = tk.Toplevel(self.master)
        top.title("Choose Font Size")
        scale = tk.Scale(top, from_=8, to=13, orient=tk.HORIZONTAL)  # Limit the font size to 16
        scale.set(self.font_size)
        scale.pack(padx=10, pady=10)

        def apply():
            self.font_size = scale.get()
            self.message_area.configure(font=(self.font_family, self.font_size))
            top.destroy()

        tk.Button(top, text="Apply", command=apply).pack(pady=5)

    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        self.update_bubble_colors()
        self.update_theme_styles()

    def update_bubble_colors(self):
        if self.theme == "dark":
            self.send_color = self.send_color_dark
            self.receive_color = self.receive_color_dark
        else:
            self.send_color = self.send_color_light
            self.receive_color = self.receive_color_light

        self.message_area.tag_configure("right_bubble", background=self.send_color)
        self.message_area.tag_configure("left_bubble", background=self.receive_color)

    def update_theme_styles(self):
        bg = self.bg_dark if self.theme == "dark" else self.bg_light
        fg = self.text_dark if self.theme == "dark" else self.text_light

        self.master.configure(bg=bg)
        self.main_frame.configure(bg=bg)
        self.toolbar.configure(bg=bg)
        self.status_frame.configure(bg=bg)
        self.status_label.configure(bg=bg, fg=fg)
        self.message_area.configure(bg=bg, fg=fg, insertbackground=fg)
        self.input_frame.configure(bg=bg)
        self.message_entry.configure(bg=bg, fg=fg, insertbackground=fg)

    def open_color_chooser(self):
        def choose_send_color():
            color = colorchooser.askcolor(title="Choose Sent Message Color")[1]
            if color:
                self.send_color = color
                self.message_area.tag_configure("right_bubble", background=self.send_color)

        def choose_receive_color():
            color_tuple = colorchooser.askcolor(title="Choose Received Message Color")
            color = color_tuple[1]  # The hex string like "#aabbcc"

            if color is not None:
                self.receive_color = color
                self.message_area.tag_configure("left_bubble", background=self.receive_color)

        chooser = tk.Toplevel(self.master)
        chooser.title("Change Bubble Colors")
        chooser.geometry("350x150")
        chooser.grab_set()

        tk.Label(chooser, text="Choose new bubble colors:", font=("Arial", 13)).pack(pady=10)

        button_frame = tk.Frame(chooser)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Sent Message Color", width=20, command=choose_send_color).pack(
            side=tk.LEFT, padx=10
        )
        tk.Button(button_frame, text="Received Message Color", width=20, command=choose_receive_color).pack(
            side=tk.RIGHT, padx=10
        )

        tk.Button(chooser, text="Close", command=chooser.destroy).pack(pady=10)

    def connect_to_server(self):
        try:
            self.user_socket = PictureEncryptionSocket(self.host)
            self.display_message_local("System: Connecting...\n")
            self.user_socket.connect()
            self.is_connected = True
            self.stop_thread = False
            self.status_label.config(text=f"Status: Connected to {self.host}", fg="green")
            self.display_message_local(f"System: Connected as {self.username}.\n")

            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()

        except socket.timeout:
            self.display_message_local(f"System: Connection timed out. Could not reach {self.host}.\n")
            messagebox.showerror(
                "Connection Error", f"Connection timed out trying to reach {self.host}", parent=self.master
            )
            self.on_closing(show_error=False)
        except (socket.error, ConnectionRefusedError) as e:
            self.display_message_local(f"System: Connection error: {e}\n")
            messagebox.showerror(
                "Connection Error", f"Could not connect to server at {self.host}\nError: {e}", parent=self.master
            )
            self.on_closing(show_error=False)
        except Exception as e:
            self.display_message_local(f"System: An unexpected error occurred: {e}\n")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self.master)
            self.on_closing(show_error=False)

    def receive_messages(self):
        while self.is_connected and not self.stop_thread:
            try:
                print(333)
                message = self.user_socket.receive()
                print(222)
                if not message:
                    self.display_message_local("\nSystem: Server closed the connection.\n")
                    self.master.after(0, self.handle_disconnection)
                    break

                decoded_message = message.decode(ENCODING)
                self.master.after(0, self.display_message_remote, decoded_message)

            except (socket.error, ConnectionResetError, BrokenPipeError, Exception) as e:
                print(1)
                if not self.stop_thread:
                    print(2)
                    self.display_message_local(f"\nSystem: Connection error: {e}\n")
                    self.master.after(0, self.handle_disconnection)
                break

            except Exception as e:
                if not self.stop_thread:
                    self.display_message_local(f"\nSystem: Error receiving message: {e}\n")
                    self.master.after(0, self.handle_disconnection)
                break

    def handle_disconnection(self):
        if self.is_connected:
            self.is_connected = False
            self.status_label.config(text="Status: Disconnected", fg="red")
            self.message_entry.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            messagebox.showinfo("Disconnected", "Lost connection to the server.", parent=self.master)

    def send_message_event(self, event=None):
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "You are not connected to the server.", parent=self.master)
            return

        message = self.message_entry.get()
        if message:
            try:
                timestamp = datetime.now().strftime("%I:%M %p")
                full_message = f"{self.username} [{timestamp}]: {message}"
                self.user_socket.send(full_message.encode(ENCODING))
                self.display_message_local(f"You [{timestamp}]: {message}")
                self.message_entry.delete(0, tk.END)
            except (socket.error, BrokenPipeError) as e:
                self.display_message_local(f"\nSystem: Failed to send message: {e}\n")
                self.handle_disconnection()
                self.stop_thread = True
                if self.user_socket:
                    try:
                        self.user_socket.close()
                    except socket.error:
                        pass
                    self.user_socket = None

    def display_message_local(self, message):
        self.message_area.configure(state=tk.NORMAL)
        self.message_area.insert(tk.END, message + "\n", "right_bubble")  # Add newline for each message
        self.message_area.configure(state=tk.DISABLED)
        self.message_area.yview(tk.END)

    def display_message_remote(self, message):
        self.message_area.configure(state=tk.NORMAL)
        self.message_area.insert(tk.END, message + "\n", "left_bubble")  # Add newline for each message
        self.message_area.configure(state=tk.DISABLED)
        self.message_area.yview(tk.END)

    def send_message(self, message):
        self.display_message_local(f"{self.username}: {message}\n")
        self.user_socket.send(message.encode(ENCODING))
        self.message_entry.delete(0, tk.END)

    def on_closing(self, show_error=True):
        if show_error and self.is_connected:
            if not messagebox.askokcancel("Quit", "Do you want to disconnect and quit?", parent=self.master):
                return

        self.stop_thread = True
        self.is_connected = False

        if self.user_socket:
            try:
                self.user_socket.close()
            except socket.error:
                pass
            self.user_socket = None

        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
