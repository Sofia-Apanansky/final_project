import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import socket
import threading
import sys
import time

from picture_encryption_socket import PictureEncryptionSocket

ENCODING = 'utf-8'


class ChatClient:
    def __init__(self, master):
        self.master = master
        self.client_socket: PictureEncryptionSocket = None
        self.receive_thread = None
        self.is_connected = False
        self.stop_thread = False  # Flag to signal thread termination

        # --- Get Server Info ---
        # Use simpledialog for initial setup
        self.host = simpledialog.askstring("Server Address", "Enter server IP:", parent=master)
        if not self.host:  # User cancelled
            master.destroy()
            sys.exit("Connection cancelled by user.")

        self.username = simpledialog.askstring("Username", "Enter your username:", parent=master)
        if not self.username:  # User cancelled or entered empty
            self.username = f"User_{int(time.time()) % 10000}"  # Default username
            messagebox.showwarning("Username", f"No username entered. Using default: {self.username}", parent=master)

        # --- GUI Setup ---
        master.title(f"Chat Client - {self.username}")
        master.geometry("450x550")  # Adjusted size

        # Frame for connection status/buttons (optional)
        self.status_frame = tk.Frame(master)
        self.status_frame.pack(pady=5)
        self.status_label = tk.Label(self.status_frame, text="Status: Disconnected", fg="red")
        self.status_label.pack()

        # Message display area
        self.message_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, state=tk.DISABLED)  # Start disabled
        self.message_area.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        # Input frame
        self.input_frame = tk.Frame(master)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X)

        # Message entry field
        self.message_entry = tk.Entry(self.input_frame, width=40)
        self.message_entry.bind("<Return>", self.send_message_event)  # Send on Enter key
        self.message_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Send button
        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message_event)
        self.send_button.pack(side=tk.RIGHT, padx=5)

        # Set focus to entry field initially
        self.message_entry.focus_set()

        # Handle window closing
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Start Connection ---
        self.connect_to_server()

    def connect_to_server(self):
        """Establishes connection to the server."""
        try:
            self.client_socket = PictureEncryptionSocket(self.host)
            self.display_message_local("System: Connecting...\n")
            self.client_socket.connect()
            self.is_connected = True
            self.stop_thread = False  # Reset stop flag before starting thread
            self.status_label.config(text=f"Status: Connected to {self.host}", fg="green")
            self.display_message_local(f"System: Connected as {self.username}.\n")

            # Start the receiving thread
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()

        except socket.timeout:
            self.display_message_local(f"System: Connection timed out. Could not reach {self.host}.\n")
            messagebox.showerror("Connection Error", f"Connection timed out trying to reach {self.host}",
                                 parent=self.master)
            self.on_closing(show_error=False)  # Use closing logic to clean up
        except (socket.error, ConnectionRefusedError) as e:
            self.display_message_local(f"System: Connection error: {e}\n")
            messagebox.showerror("Connection Error",
                                 f"Could not connect to server at {self.host}\nError: {e}",
                                 parent=self.master)
            self.on_closing(show_error=False)  # Clean up
        except Exception as e:  # Catch other potential errors during setup
            self.display_message_local(f"System: An unexpected error occurred: {e}\n")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self.master)
            self.on_closing(show_error=False)

    def receive_messages(self):
        """Receives messages from the server in a separate thread."""
        while self.is_connected and not self.stop_thread:
            try:
                message = self.client_socket.receive()
                if not message:
                    # Server disconnected gracefully
                    self.display_message_local("\nSystem: Server closed the connection.\n")
                    # Schedule GUI update in main thread
                    self.master.after(0, self.handle_disconnection)
                    break  # Exit thread loop

                # Decode and schedule display in main thread
                decoded_message = message.decode(ENCODING)
                # Schedule the display_message function to run in the main GUI thread
                self.master.after(0, self.display_message_remote, decoded_message + "\n")

            except (socket.error, ConnectionResetError, BrokenPipeError) as e:
                if not self.stop_thread:  # Don't show error if we initiated the closing
                    self.display_message_local(f"\nSystem: Connection error: {e}\n")
                    # Schedule GUI update in main thread
                    self.master.after(0, self.handle_disconnection)
                break  # Exit thread loop
            except Exception as e:  # Catch other potential errors during recv
                if not self.stop_thread:
                    self.display_message_local(f"\nSystem: Error receiving message: {e}\n")
                    self.master.after(0, self.handle_disconnection)
                break  # Exit thread loop

        print("Receive thread finished.")  # Debug print

    def handle_disconnection(self):
        """ Cleans up GUI state after disconnection, called from main thread """
        if self.is_connected:  # Avoid multiple calls
            self.is_connected = False
            self.status_label.config(text="Status: Disconnected", fg="red")
            self.message_entry.config(state=tk.DISABLED)  # Disable input
            self.send_button.config(state=tk.DISABLED)  # Disable send button
            messagebox.showinfo("Disconnected", "Lost connection to the server.", parent=self.master)
            # Don't close the socket here, on_closing handles that

    def send_message_event(self, event=None):  # event=None allows calling it from button click too
        """Gets message from entry field and sends it."""
        if not self.is_connected:
            messagebox.showwarning("Not Connected", "You are not connected to the server.", parent=self.master)
            return

        message = self.message_entry.get()
        if message:
            try:
                # Prepend username to the message
                full_message = f"{self.username}: {message}"
                self.client_socket.send(full_message.encode(ENCODING))
                self.display_message_local(f"You: {message}\n")  # Display sent message locally
                self.message_entry.delete(0, tk.END)  # Clear the entry field
            except (socket.error, BrokenPipeError) as e:
                self.display_message_local(f"\nSystem: Failed to send message: {e}\n")
                # Disconnect if send fails critically
                self.handle_disconnection()  # Update GUI state immediately
                # Signal thread to stop and close socket (will happen in on_closing or when thread exits)
                self.stop_thread = True
                if self.client_socket:
                    try:
                        self.client_socket.close() # TODO add close to socket
                    except socket.error:
                        pass
                    self.client_socket = None

    def display_message_local(self, message):
        """ Displays a message (e.g., system status, own messages) in the text area. """
        # This can be called from the main thread directly
        self.message_area.config(state=tk.NORMAL)  # Enable writing
        self.message_area.insert(tk.END, message)
        self.message_area.see(tk.END)  # Scroll to the bottom
        self.message_area.config(state=tk.DISABLED)  # Disable writing

    def display_message_remote(self, message):
        """ Displays a received message - MUST be called via root.after from receive thread. """
        # This runs in the main thread
        self.message_area.config(state=tk.NORMAL)
        self.message_area.insert(tk.END, message)
        self.message_area.see(tk.END)
        self.message_area.config(state=tk.DISABLED)

    def on_closing(self, show_error=True):
        """Handles window closing: stops thread, closes socket, destroys window."""
        if show_error and self.is_connected:
            if not messagebox.askokcancel("Quit", "Do you want to disconnect and quit?", parent=self.master):
                return  # User cancelled closing

        print("Closing application...")
        self.stop_thread = True  # Signal the receiving thread to stop
        self.is_connected = False  # Update connection status

        if self.client_socket:
            try:
                # Optionally send a "disconnecting" message
                # self.client_socket.sendall(f"{self.username} is disconnecting.".encode(ENCODING))
                # Shutdown signals intent to close, can help unblock recv on server faster
                self.client_socket.shutdown(socket.SHUT_RDWR) # TODO
            except (socket.error, OSError):
                print("Error during socket shutdown (already closed or broken?).")  # Ignore errors here
            finally:
                try:
                    self.client_socket.close() # TODO
                except socket.error:
                    pass  # Ignore if already closed
                self.client_socket = None
                print("Client socket closed.")

        # Wait briefly for the thread to notice the flag (optional, but good practice)
        # if self.receive_thread and self.receive_thread.is_alive():
        #     self.receive_thread.join(timeout=0.5) # Wait max 0.5 sec

        print("Destroying master window.")
        self.master.destroy()
        # Ensure the script exits if the window is closed externally
        sys.exit(0)


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()  # Start the Tkinter event loop
