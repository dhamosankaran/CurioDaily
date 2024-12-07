import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

class PersonalDiary:
    def __init__(self, root):
        self.root = root
        self.root.title("My Personal Diary")
        self.root.geometry("800x600")
        
        # Set up the main container with a nice background
        self.style = ttk.Style()
        self.style.configure("Main.TFrame", background="#f0f0f5")
        self.main_frame = ttk.Frame(root, style="Main.TFrame", padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        self.welcome_label = ttk.Label(
            self.main_frame,
            text="Welcome to Your Personal Diary",
            font=("Helvetica", 24),
            background="#f0f0f5"
        )
        self.welcome_label.pack(pady=20)
        
        # Date display
        self.date_label = ttk.Label(
            self.main_frame,
            text=f"Date: {datetime.now().strftime('%B %d, %Y')}",
            font=("Helvetica", 12),
            background="#f0f0f5"
        )
        self.date_label.pack(pady=10)
        
        # Entry title
        self.title_label = ttk.Label(
            self.main_frame,
            text="Entry Title:",
            background="#f0f0f5"
        )
        self.title_label.pack(pady=5)
        
        self.title_entry = ttk.Entry(self.main_frame, width=50)
        self.title_entry.pack(pady=5)
        
        # Entry content
        self.content_label = ttk.Label(
            self.main_frame,
            text="Your Thoughts:",
            background="#f0f0f5"
        )
        self.content_label.pack(pady=5)
        
        # Text widget for diary entry
        self.text_widget = tk.Text(
            self.main_frame,
            height=15,
            width=70,
            font=("Helvetica", 11),
            wrap=tk.WORD
        )
        self.text_widget.pack(pady=10)
        
        # Buttons frame
        self.button_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.button_frame.pack(pady=20)
        
        # Save button
        self.save_button = ttk.Button(
            self.button_frame,
            text="Save Entry",
            command=self.save_entry
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # View previous entries button
        self.view_button = ttk.Button(
            self.button_frame,
            text="View Previous Entries",
            command=self.view_entries
        )
        self.view_button.pack(side=tk.LEFT, padx=5)
        
        # Create diary directory if it doesn't exist
        self.diary_dir = os.path.expanduser("~/Documents/MyPersonalDiary")
        if not os.path.exists(self.diary_dir):
            os.makedirs(self.diary_dir)
    
    def save_entry(self):
        """Save the diary entry to a JSON file"""
        if not self.title_entry.get() or not self.text_widget.get("1.0", tk.END).strip():
            messagebox.showwarning("Warning", "Please enter both title and content!")
            return
            
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": self.title_entry.get(),
            "content": self.text_widget.get("1.0", tk.END).strip()
        }
        
        filename = os.path.join(
            self.diary_dir,
            f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(filename, 'w') as f:
            json.dump(entry, f, indent=4)
            
        messagebox.showinfo("Success", "Diary entry saved successfully!")
        self.clear_fields()
    
    def clear_fields(self):
        """Clear the input fields"""
        self.title_entry.delete(0, tk.END)
        self.text_widget.delete("1.0", tk.END)
    
    def view_entries(self):
        """Open a new window to view previous entries"""
        view_window = tk.Toplevel(self.root)
        view_window.title("Previous Entries")
        view_window.geometry("600x400")
        
        # Create a frame for the entries
        entries_frame = ttk.Frame(view_window, padding="20")
        entries_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a scrolled text widget to display entries
        entries_text = tk.Text(
            entries_frame,
            height=20,
            width=60,
            wrap=tk.WORD,
            font=("Helvetica", 11)
        )
        entries_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(entries_frame, orient=tk.VERTICAL, command=entries_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        entries_text.configure(yscrollcommand=scrollbar.set)
        
        # Load and display entries
        entries = []
        for filename in sorted(os.listdir(self.diary_dir), reverse=True):
            if filename.endswith('.json'):
                with open(os.path.join(self.diary_dir, filename), 'r') as f:
                    entry = json.load(f)
                    entries.append(entry)
        
        for entry in entries:
            entries_text.insert(tk.END, f"\nDate: {entry['date']}\n")
            entries_text.insert(tk.END, f"Title: {entry['title']}\n")
            entries_text.insert(tk.END, f"Content:\n{entry['content']}\n")
            entries_text.insert(tk.END, "\n" + "-"*50 + "\n")
        
        entries_text.configure(state='disabled')  # Make text read-only

# Main application runner
if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalDiary(root)
    root.mainloop()