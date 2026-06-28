import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json
import os
import re

# --- Default Fallback Formations ---
DEFAULT_FORMATIONS = {
    "2-3-1 (Balanced)": {
        "description": (
            "The 2-3-1 is the most popular 7-a-side formation.\n\n"
            "Provides a solid defensive base with 2 Defenders, a compact "
            "midfield of 3 to control possession, and 1 dedicated Striker."
        ),
        "players": [
            {"id": "GK", "pos": [200, 480], "color": "#FFCC00"},
            {"id": "LD", "pos": [120, 380], "color": "#3399FF"},
            {"id": "RD", "pos": [280, 380], "color": "#3399FF"},
            {"id": "LM", "pos": [70, 240], "color": "#33CC66"},
            {"id": "CM", "pos": [200, 270], "color": "#33CC66"},
            {"id": "RM", "pos": [330, 240], "color": "#33CC66"},
            {"id": "ST", "pos": [200, 100], "color": "#FF5050"}
        ],
        "bench": [
            {"id": "SUB1", "color": "#94a3b8"}, {"id": "SUB2", "color": "#94a3b8"},
            {"id": "SUB3", "color": "#94a3b8"}, {"id": "SUB4", "color": "#94a3b8"},
            {"id": "SUB5", "color": "#94a3b8"}, {"id": "SUB6", "color": "#94a3b8"},
            {"id": "SUB7", "color": "#94a3b8"}, {"id": "SUB8", "color": "#94a3b8"},
            {"id": "SUB9", "color": "#94a3b8"}, {"id": "SB10", "color": "#94a3b8"}
        ],
        "lines": []  # Preset vector paths
    }
}

DATA_FILE = "formations_data.json"
BENCH_Y_START = 550

class SoccerFormationApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("7-A-Side Soccer Board (with Drawing & Subs)")
        self.geometry("1200x780")
        self.minsize(1100, 700)
        
        self.load_data()
        
        # State tracking flags
        self.selected_player_id = None
        self.is_selected_from_bench = False
        self.draw_start_pos = None
        self.temp_draw_line = None
        
        # Free-drawn temporary lines session memory storage array
        self.custom_drawn_lines = []
        
        self.setup_styles()
        self.create_widgets()
        self.update_display()

    def load_data(self):
        global FORMATIONS
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    FORMATIONS = json.load(f)
                self.current_formation = list(FORMATIONS.keys())[0]
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read data file. Restoring defaults.\n{e}")
                FORMATIONS = DEFAULT_FORMATIONS.copy()
                self.current_formation = "2-3-1 (Balanced)"
        else:
            FORMATIONS = DEFAULT_FORMATIONS.copy()
            self.current_formation = "2-3-1 (Balanced)"
            
        for form in FORMATIONS.values():
            if "bench" not in form or len(form["bench"]) < 10:
                form["bench"] = [{"id": f"SUB{i+1}"[:4], "color": "#94a3b8"} for i in range(10)]

    def save_data_to_file(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(FORMATIONS, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data file: {e}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", font=("Helvetica", 11))
        style.configure("Header.TLabel", font=("Helvetica", 13, "bold"))
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground="#1e293b")
        style.configure("Action.TButton", font=("Helvetica", 11, "bold"), padding=5)

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(top_frame, text="Select Strategy:", style="Header.TLabel").pack(side=tk.LEFT, padx=5)
        
        self.formation_combo = ttk.Combobox(
            top_frame, values=list(FORMATIONS.keys()), state="readonly", font=("Helvetica", 11), width=21
        )
        self.formation_combo.set(self.current_formation)
        self.formation_combo.pack(side=tk.LEFT, padx=5)
        self.formation_combo.bind("<<ComboboxSelected>>", self.on_formation_change)

        ttk.Button(top_frame, text="➕ Add Formation", style="Action.TButton", command=self.create_custom_formation).pack(side=tk.LEFT, padx=5)
        
        # New Feature Button: Clear Free-drawn run routes vectors canvas markers overlay layer
        ttk.Button(top_frame, text="🧹 Clear Drawn Lines", style="Action.TButton", command=self.clear_drawn_lines).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="📥 Import", style="Action.TButton", command=self.import_from_txt).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Export 📤", style="Action.TButton", command=self.export_to_txt).pack(side=tk.RIGHT, padx=5)

        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- LEFT SIDE ---
        left_frame = ttk.Frame(main_paned, padding=10)
        main_paned.add(left_frame, weight=1)

        self.info_title = ttk.Label(left_frame, text="", style="Title.TLabel")
        self.info_title.pack(anchor=tk.W, pady=(0, 5))

        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        self.text_window = tk.Text(
            left_frame, wrap=tk.WORD, font=("Helvetica", 11), bg="#ffffff", fg="#334155", bd=1, relief="solid", padx=10, pady=10, undo=True
        )
        self.text_window.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(left_frame, text="💾 Save Current Notes", command=self.save_text_notes).pack(fill=tk.X, pady=(5, 0))
        
        legend_frame = ttk.LabelFrame(left_frame, text=" Tactics Board Instructions ", padding=8)
        legend_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(legend_frame, text="✍ Draw Run Arrow: Hold 'Shift' + Drag mouse across the field.", font=("Helvetica", 10, "bold"), foreground="#d97706").pack(anchor=tk.W)
        ttk.Label(legend_frame, text="🏃 Drag Players: Drag mouse normally (without Shift) to move names around.", font=("Helvetica", 10)).pack(anchor=tk.W)

        # --- RIGHT SIDE ---
        right_frame = ttk.Frame(main_paned, padding=10)
        main_paned.add(right_frame, weight=1)

        self.canvas = tk.Canvas(right_frame, width=420, height=680, bg="#2e7d32", highlightthickness=2, highlightbackground="#1b5e20")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Interactive Event Triggers
        self.canvas.bind("<ButtonPress-1>", self.on_pitch_press)
        self.canvas.bind("<B1-Motion>", self.on_pitch_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_pitch_release)
        self.canvas.bind("<Double-Button-1>", self.on_player_double_click)

    def clear_drawn_lines(self):
        self.custom_drawn_lines = []
        self.redraw_canvas()

    def save_text_notes(self):
        FORMATIONS[self.current_formation]["description"] = self.text_window.get("1.0", tk.END).strip()
        self.save_data_to_file()
        messagebox.showinfo("Saved", "Tactical notes successfully updated!")

    def export_to_txt(self):
        formation_data = FORMATIONS[self.current_formation]
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"STRATEGY NAME: {self.current_formation}\n")
                    f.write(f"==================================================\n")
                    f.write(f"[STRATEGY & DRILL DESCRIPTION NOTES]\n{self.text_window.get('1.0', tk.END).strip()}\n\n")
                    f.write(f"--------------------------------------------------\n[PITCH PLAYERS]\n")
                    for p in formation_data["players"]:
                        f.write(f"Player: {p['id']} | Color: {p['color']} | X={p['pos'][0]}, Y={p['pos'][1]}\n")
                    f.write(f"\n[BENCH SUBSTITUTES]\n")
                    for b in formation_data["bench"]:
                        f.write(f"BenchSub: {b['id']} | Color: {b['color']}\n")
                messagebox.showinfo("Export Complete", "Strategy report exported successfully!")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def import_from_txt(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path: return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            name_match = re.search(r"STRATEGY NAME:\s*(.*)", content)
            s_name = name_match.group(1).strip() if name_match else "Imported Layout"
            if s_name in FORMATIONS: s_name += " (Copy)"

            desc = ""
            split_content = content.split("[STRATEGY & DRILL DESCRIPTION NOTES]\n")
            if len(split_content) > 1:
                desc = split_content[1].split("--------------------------------------------------")[0].strip()

            p_lines = re.findall(r"Player:\s*(\S+)\s*\|\s*Color:\s*(\S+)\s*\|\s*X=(\d+),\s*Y=(\d+)", content)
            if not p_lines: return

            players = [{"id": pid[:5], "pos": [int(x), int(y)], "color": col} for pid, col, x, y in p_lines]
            b_lines = re.findall(r"BenchSub:\s*(\S+)\s*\|\s*Color:\s*(\S+)", content)
            bench = [{"id": bid[:5], "color": col} for bid, col in b_lines]
            if len(bench) < 10:
                bench += [{"id": f"SUB{i+1}", "color": "#94a3b8"} for i in range(len(bench), 10)]

            FORMATIONS[s_name] = {"description": desc, "players": players, "bench": bench[:10], "lines": []}
            self.save_data_to_file()
            self.formation_combo["values"] = list(FORMATIONS.keys())
            self.formation_combo.set(s_name)
            self.current_formation = s_name
            self.update_display()
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def create_custom_formation(self):
        name = simpledialog.askstring("New Strategy", "Enter strategy label:")
        if not name or name.strip() == "": return
        name = name.strip()
        if name in FORMATIONS: return

        FORMATIONS[name] = {
            "description": "Custom routines data guidelines text field details sheet.",
            "players": [
                {"id": "GK", "pos": [200, 480], "color": "#FFCC00"}, {"id": "P2", "pos": [100, 380], "color": "#3399FF"},
                {"id": "P3", "pos": [300, 380], "color": "#3399FF"}, {"id": "P4", "pos": [200, 260], "color": "#33CC66"},
                {"id": "P5", "pos": [100, 180], "color": "#33CC66"}, {"id": "P6", "pos": [300, 180], "color": "#33CC66"},
                {"id": "P7", "pos": [200, 90], "color": "#FF5050"}
            ],
            "bench": [{"id": f"SUB{i+1}", "color": "#94a3b8"} for i in range(10)],
            "lines": []
        }
        self.save_data_to_file()
        self.formation_combo["values"] = list(FORMATIONS.keys())
        self.formation_combo.set(name)
        self.current_formation = name
        self.clear_drawn_lines()
        self.update_display()

    def on_formation_change(self, event):
        self.current_formation = self.formation_combo.get()
        self.clear_drawn_lines()
        self.update_display()

    def update_display(self):
        self.info_title.config(text=self.current_formation)
        self.text_window.delete("1.0", tk.END)
        self.text_window.insert(tk.END, FORMATIONS[self.current_formation]["description"])
        self.redraw_canvas()

    def redraw_canvas(self):
        formation_data = FORMATIONS[self.current_formation]
        self.canvas.delete("all")
        
        # Pitch Boundary Lines Layout setup marking
        self.canvas.create_rectangle(15, 15, 395, 520, outline="white", width=2)
        self.canvas.create_line(15, 265, 395, 265, fill="white", width=2)
        self.canvas.create_oval(140, 205, 260, 325, outline="white", width=2)
        self.canvas.create_rectangle(90, 15, 310, 90, outline="white", width=2)
        self.canvas.create_rectangle(90, 445, 310, 520, outline="white", width=2)

        # Draw Substitutes Bench Area container module
        self.canvas.create_rectangle(5, 535, 405, 670, fill="#1e293b", outline="#475569", width=2)
        self.canvas.create_text(85, 550, text="SQUAD BENCH (SHIFT+DRAG TO DRAW RUN LINES)", fill="#94a3b8", font=("Helvetica", 8, "bold"))

        # Render Core Default Preset Strategy lines vectors layout
        player_map = {p["id"]: p["pos"] for p in formation_data["players"]}
        for line in formation_data["lines"]:
            start_id, end_id, l_type = line
            if start_id in player_map and end_id in player_map:
                x1, y1 = player_map[start_id]
                x2, y2 = player_map[end_id]
                if l_type == "pass":
                    self.canvas.create_line(x1, y1, x2, y2, fill="#ffffff", width=2)

        # Render Free-Hand Coach Custom drawn run routes vectors paths overlay layer cache list 
        for line in self.custom_drawn_lines:
            self.canvas.create_line(line[0], line[1], line[2], line[3], fill="#FFD700", width=2, dash=(5, 3), arrow=tk.LAST)

        # Draw Active Lineup Field Position Tokens
        r = 15 
        for p in formation_data["players"]:
            x, y = p["pos"]
            self.canvas.create_oval(x - r + 2, y - r + 2, x + r + 2, y + r + 2, fill="#0f172a", outline="")
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=p["color"], outline="white", width=2)
            self.canvas.create_text(x, y, text=p["id"], fill="black" if p["color"] == "#FFCC00" else "white", font=("Helvetica", 9, "bold"))

        # Draw 10 Substitute Grid Positions
        for i, b in enumerate(formation_data["bench"]):
            col = i % 5
            row = i // 5
            bx = 50 + (col * 75)
            by = 585 + (row * 50)
            b["_bench_home_pos"] = [bx, by]
            self.canvas.create_oval(bx - r, by - r, bx + r, by + r, fill=b["color"], outline="#cbd5e1", width=1)
            self.canvas.create_text(bx, by, text=b["id"], fill="white", font=("Helvetica", 8, "bold"))

    # --- Mouse Tracking Matrix Logic with Drawing Tool integration ---
    def on_pitch_press(self, event):
        formation_data = FORMATIONS[self.current_formation]
        cx, cy = event.x, event.y
        r = 16
        
        # DRAW OPERATION BRANCH: Triggers when the user is holding down keyboard shift key
        if event.state & 0x0001:  # Shift Key Mask code check flag state
            self.draw_start_pos = (cx, cy)
            return

        # STANDARD MOVE SYSTEM
        self.draw_start_pos = None
        for p in formation_data["players"]:
            px, py = p["pos"]
            if (cx - px)**2 + (cy - py)**2 <= r**2:
                self.selected_player_id = p["id"]
                self.is_selected_from_bench = False
                return
                
        for b in formation_data["bench"]:
            if "_bench_home_pos" in b:
                bx, by = b["_bench_home_pos"]
                if (cx - bx)**2 + (cy - by)**2 <= r**2:
                    self.selected_player_id = b["id"]
                    self.is_selected_from_bench = True
                    return

    def on_pitch_drag(self, event):
        nx = max(20, min(event.x, 390))
        ny = max(20, min(event.y, 660))

        # Dynamic Draw Routing logic calculations
        if self.draw_start_pos:
            if self.temp_draw_line:
                self.canvas.delete(self.temp_draw_line)
            # Preview dotted trace dynamically tracking behind real-time mouse path coordinates trace
            self.temp_draw_line = self.canvas.create_line(
                self.draw_start_pos[0], self.draw_start_pos[1], nx, ny, 
                fill="#FFD700", width=2, dash=(5, 3), arrow=tk.LAST
            )
            return

        # Regular player position update calculations handling
        if not self.selected_player_id: return
        formation_data = FORMATIONS[self.current_formation]

        if not self.is_selected_from_bench:
            for p in formation_data["players"]:
                if p["id"] == self.selected_player_id:
                    p["pos"] = [nx, ny]
                    break
        self.redraw_canvas()

        if self.is_selected_from_bench:
            self.canvas.create_oval(nx - 14, ny - 14, nx + 14, ny + 14, fill="#64748b", outline="yellow", width=2)
            self.canvas.create_text(nx, ny, text=self.selected_player_id, fill="white", font=("Helvetica", 8, "bold"))

    def on_pitch_release(self, event):
        formation_data = FORMATIONS[self.current_formation]
        
        # Commit drawn run path vectors coordinates into canvas layer cache lists
        if self.draw_start_pos:
            nx = max(20, min(event.x, 390))
            ny = max(20, min(event.y, 660))
            # Only append line vector if line length cross min register threshold rules limits
            if (nx - self.draw_start_pos[0])**2 + (ny - self.draw_start_pos[1])**2 > 10**2:
                self.custom_drawn_lines.append((self.draw_start_pos[0], self.draw_start_pos[1], nx, ny))
            self.draw_start_pos = None
            self.temp_draw_line = None
            self.redraw_canvas()
            return

        if not self.selected_player_id: return
        ry = event.y

        if self.is_selected_from_bench and ry < BENCH_Y_START:
            target_pitch_player = None
            if formation_data["players"]:
                target_pitch_player = formation_data["players"][-1]
                for p in formation_data["players"]:
                    if (event.x - p["pos"][0])**2 + (event.y - p["pos"][1])**2 <= 50**2:
                        target_pitch_player = p
                        break
            if target_pitch_player:
                for b in formation_data["bench"]:
                    if b["id"] == self.selected_player_id:
                        old_b_id, old_b_col = b["id"], b["color"]
                        b["id"], b["color"] = target_pitch_player["id"], target_pitch_player["color"]
                        target_pitch_player["id"], target_pitch_player["color"] = old_b_id, old_b_col
                        break

        elif not self.is_selected_from_bench and ry >= BENCH_Y_START:
            target_bench_item = formation_data["bench"][0]
            for b in formation_data["bench"]:
                bx, by = b["_bench_home_pos"]
                if (event.x - bx)**2 + (event.y - by)**2 <= 40**2:
                    target_bench_item = b
                    break
            for p in formation_data["players"]:
                if p["id"] == self.selected_player_id:
                    old_p_id, old_p_col = p["id"], p["color"]
                    p["id"], p["color"] = target_bench_item["id"], target_bench_item["color"]
                    target_bench_item["id"], target_bench_item["color"] = old_p_id, old_p_col
                    p["pos"] = [200, 450]
                    break

        self.save_data_to_file()
        self.selected_player_id = None
        self.redraw_canvas()

    def on_player_double_click(self, event):
        formation_data = FORMATIONS[self.current_formation]
        cx, cy = event.x, event.y
        r = 16
        target_item = None

        for p in formation_data["players"]:
            if (cx - p["pos"][0])**2 + (cy - p["pos"][1])**2 <= r**2:
                target_item = p
                break
        if not target_item:
            for b in formation_data["bench"]:
                bx, by = b["_bench_home_pos"]
                if (cx - bx)**2 + (cy - by)**2 <= r**2:
                    target_item = b
                    break

        if target_item:
            new_name = simpledialog.askstring("Rename", f"Enter name/initials for {target_item['id']}:", initialvalue=target_item["id"], parent=self)
            if new_name and new_name.strip() != "":
                target_item["id"] = new_name.strip()[:5]
                self.save_data_to_file()
                self.redraw_canvas()


if __name__ == "__main__":
    app = SoccerFormationApp()
    app.mainloop()