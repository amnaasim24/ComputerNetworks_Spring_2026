"""
DNS Resolver & Query Analyzer
==============================
Computer Networks Course Project
Uses: dnspython, tkinter, matplotlib, time, datetime

How to run:
    pip install dnspython matplotlib
    python dns_resolver_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import dns.resolver
import time
from datetime import datetime
import matplotlib
matplotlib.use("Agg")           # Use non-interactive backend (safe for Tkinter)
import matplotlib.pyplot as plt
import os
import subprocess
import sys

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

# Save directory – change this if needed
SAVE_DIR = r"C:\Users\DC\Desktop\CN Project"
LOG_FILE = os.path.join(SAVE_DIR, "dns_logs.txt")
GRAPH_FILE = os.path.join(SAVE_DIR, "dns_performance_graph.png")

# DNS servers to query
DNS_SERVERS = {
    "Google DNS":    "8.8.8.8",
    "Cloudflare DNS": "1.1.1.1",
    "OpenDNS":       "208.67.222.222",
}

# Supported record types
RECORD_TYPES = ["A", "AAAA", "MX", "NS", "CNAME"]


# ─────────────────────────────────────────────
#  DNS QUERY LOGIC
# ─────────────────────────────────────────────

def query_dns(domain, record_type, server_ip):
    """
    Query a single DNS server for a domain's record type.
    Returns a dict with records, TTL, and response time.
    On error, returns an error message instead of records.
    """
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [server_ip]
    resolver.lifetime = 5  # 5-second timeout per query

    start = time.time()
    try:
        answer = resolver.resolve(domain, record_type)
        elapsed_ms = (time.time() - start) * 1000  # convert to milliseconds

        records = []
        ttl = answer.rrset.ttl  # Time-To-Live value

        for rdata in answer:
            records.append(str(rdata))

        return {
            "success": True,
            "records": records,
            "ttl": ttl,
            "response_time_ms": round(elapsed_ms, 2),
            "error": None,
        }

    except dns.resolver.NXDOMAIN:
        # Domain does not exist
        return {"success": False, "error": "Domain not found (NXDOMAIN)"}
    except dns.resolver.NoAnswer:
        # Server responded but had no records of that type
        return {"success": False, "error": f"No {record_type} records found"}
    except dns.resolver.Timeout:
        # Server did not respond in time
        return {"success": False, "error": "Query timed out"}
    except dns.resolver.NoNameservers:
        # No name servers available
        return {"success": False, "error": "No nameservers available"}
    except Exception as e:
        # Catch-all for unexpected errors
        return {"success": False, "error": str(e)}


def run_all_queries(domain, record_type):
    """
    Query all three DNS servers and collect results.
    Returns a list of result dicts (one per server).
    """
    results = []
    for server_name, server_ip in DNS_SERVERS.items():
        result = query_dns(domain, record_type, server_ip)
        result["server_name"] = server_name
        result["server_ip"] = server_ip
        results.append(result)
    return results


# ─────────────────────────────────────────────
#  FILE + GRAPH HELPERS
# ─────────────────────────────────────────────

def ensure_save_dir():
    """Create the save directory if it doesn't exist yet."""
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_log(domain, record_type, results):
    """Append query results to the log text file."""
    ensure_save_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"Timestamp  : {timestamp}\n")
        f.write(f"Domain     : {domain}\n")
        f.write(f"Record Type: {record_type}\n")
        f.write("-" * 60 + "\n")

        for r in results:
            f.write(f"\n[{r['server_name']}]  IP: {r['server_ip']}\n")
            if r["success"]:
                f.write(f"  Records      : {', '.join(r['records'])}\n")
                f.write(f"  TTL          : {r['ttl']} seconds\n")
                f.write(f"  Response Time: {r['response_time_ms']} ms\n")
            else:
                f.write(f"  Error: {r['error']}\n")

        f.write("\n")


def save_graph(results):
    """
    Generate a bar chart of response times and save it as a PNG.
    Only includes successful queries in the chart.
    """
    ensure_save_dir()

    # Collect data for successful queries only
    labels = []
    times = []
    for r in results:
        if r["success"]:
            labels.append(r["server_name"])
            times.append(r["response_time_ms"])

    if not labels:
        return False   # Nothing to plot

    # Build the chart
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#4285F4", "#F4B400", "#0F9D58"]  # Google Blue, Yellow, Green

    bars = ax.bar(labels, times, color=colors[:len(labels)], width=0.5, edgecolor="white")

    # Add value labels on top of each bar
    for bar, val in zip(bars, times):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{val} ms",
            ha="center", va="bottom", fontsize=10, fontweight="bold"
        )

    ax.set_title("DNS Server Response Time Comparison", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("DNS Server", fontsize=11)
    ax.set_ylabel("Response Time (ms)", fontsize=11)
    ax.set_ylim(0, max(times) * 1.35 if times else 10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    plt.savefig(GRAPH_FILE, dpi=120)
    plt.close(fig)
    return True


def open_file(path):
    """Open a file with the default system application (cross-platform)."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file:\n{e}")


# ─────────────────────────────────────────────
#  MAIN GUI CLASS
# ─────────────────────────────────────────────

class DNSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Resolver & Query Analyzer")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e2e")          # Dark background
        self.root.minsize(700, 600)

        self._build_ui()

    # ── UI CONSTRUCTION ──────────────────────

    def _build_ui(self):
        """Build all widgets and lay them out."""

        # ── Color palette ──
        BG       = "#1e1e2e"
        PANEL    = "#2a2a3d"
        ACCENT   = "#7c6af7"
        TEXT     = "#e0e0f0"
        MUTED    = "#888aaa"
        BTN_BG   = "#7c6af7"
        BTN_FG   = "#ffffff"
        BTN2_BG  = "#3a3a55"
        ENTRY_BG = "#13131f"

        PAD = {"padx": 12, "pady": 6}

        # ── Title ──────────────────────────────
        title_frame = tk.Frame(self.root, bg=ACCENT, pady=10)
        title_frame.pack(fill="x")

        tk.Label(
            title_frame,
            text="🌐  DNS Resolver & Query Analyzer",
            font=("Consolas", 17, "bold"),
            bg=ACCENT, fg="#ffffff"
        ).pack()

        tk.Label(
            title_frame,
            text="Computer Networks Course Project",
            font=("Consolas", 9),
            bg=ACCENT, fg="#ddd8ff"
        ).pack()

        # ── Input Panel ────────────────────────
        input_frame = tk.Frame(self.root, bg=PANEL, pady=14, padx=20)
        input_frame.pack(fill="x", **PAD)

        # Row 1: Domain entry
        row1 = tk.Frame(input_frame, bg=PANEL)
        row1.pack(fill="x", pady=4)

        tk.Label(row1, text="Domain Name:", font=("Consolas", 10, "bold"),
                 bg=PANEL, fg=TEXT, width=14, anchor="w").pack(side="left")

        self.domain_var = tk.StringVar()
        domain_entry = tk.Entry(
            row1, textvariable=self.domain_var,
            font=("Consolas", 11), bg=ENTRY_BG, fg="#a8ffc8",
            insertbackground="#a8ffc8", relief="flat",
            highlightthickness=1, highlightbackground=ACCENT,
            width=35
        )
        domain_entry.pack(side="left", ipady=4)
        domain_entry.insert(0, "example.com")         # Placeholder hint
        # Bind Enter key to resolve
        domain_entry.bind("<Return>", lambda e: self._on_resolve())

        # Row 2: Record type + Resolve button
        row2 = tk.Frame(input_frame, bg=PANEL)
        row2.pack(fill="x", pady=8)

        tk.Label(row2, text="Record Type:", font=("Consolas", 10, "bold"),
                 bg=PANEL, fg=TEXT, width=14, anchor="w").pack(side="left")

        self.record_var = tk.StringVar(value="A")
        record_dropdown = ttk.Combobox(
            row2, textvariable=self.record_var,
            values=RECORD_TYPES, state="readonly",
            font=("Consolas", 11), width=8
        )
        record_dropdown.pack(side="left")

        # Style the dropdown
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=ENTRY_BG,
                        background=ENTRY_BG,
                        foreground="#a8ffc8",
                        selectbackground=ACCENT)

        # Resolve button
        self.resolve_btn = tk.Button(
            row2, text="▶  Resolve", font=("Consolas", 10, "bold"),
            bg=BTN_BG, fg=BTN_FG, relief="flat",
            activebackground="#6050d0", activeforeground="#ffffff",
            cursor="hand2", padx=16, pady=4,
            command=self._on_resolve
        )
        self.resolve_btn.pack(side="left", padx=(14, 0))

        # ── Status / Fastest Server Label ──────
        self.status_var = tk.StringVar(value="Enter a domain and click Resolve.")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            font=("Consolas", 10), bg="#13131f", fg="#f9c74f",
            anchor="w", padx=14, pady=6
        )
        status_bar.pack(fill="x", padx=12)

        # ── Output Text Area ───────────────────
        out_frame = tk.Frame(self.root, bg=BG)
        out_frame.pack(fill="both", expand=True, **PAD)

        tk.Label(out_frame, text="Query Results", font=("Consolas", 10, "bold"),
                 bg=BG, fg=MUTED).pack(anchor="w")

        self.output_box = scrolledtext.ScrolledText(
            out_frame,
            font=("Consolas", 10),
            bg=ENTRY_BG, fg="#c9d1d9",
            insertbackground="#c9d1d9",
            relief="flat", wrap="word",
            state="disabled",
            highlightthickness=1,
            highlightbackground=ACCENT,
            height=18
        )
        self.output_box.pack(fill="both", expand=True)

        # ── Bottom Button Row ──────────────────
        btn_frame = tk.Frame(self.root, bg=BG, pady=8)
        btn_frame.pack(fill="x", padx=12)

        btn_cfg = dict(font=("Consolas", 9, "bold"), relief="flat",
                       cursor="hand2", padx=12, pady=5)

        tk.Button(
            btn_frame, text="🗑  Clear Output",
            bg=BTN2_BG, fg=TEXT,
            activebackground="#4a4a6a",
            command=self._clear_output,
            **btn_cfg
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_frame, text="📂  Open Log File",
            bg=BTN2_BG, fg=TEXT,
            activebackground="#4a4a6a",
            command=lambda: open_file(LOG_FILE),
            **btn_cfg
        ).pack(side="left", padx=(0, 8))

        self.graph_btn = tk.Button(
            btn_frame, text="📊  View Graph",
            bg=BTN2_BG, fg=TEXT,
            activebackground="#4a4a6a",
            command=lambda: open_file(GRAPH_FILE),
            state="disabled",
            **btn_cfg
        )
        self.graph_btn.pack(side="left")

        # Footer
        tk.Label(
            self.root,
            text=f"Logs → {LOG_FILE}",
            font=("Consolas", 8), bg=BG, fg="#555577"
        ).pack(side="bottom", pady=(0, 4))

    # ── EVENT HANDLERS ───────────────────────

    def _on_resolve(self):
        """Called when the user clicks Resolve (or presses Enter)."""
        domain = self.domain_var.get().strip()
        record_type = self.record_var.get()

        # Basic validation
        if not domain:
            messagebox.showwarning("Missing Input", "Please enter a domain name.")
            return
        if " " in domain or len(domain) < 3:
            messagebox.showwarning("Invalid Domain", "Please enter a valid domain name (e.g., google.com).")
            return

        # Disable button while querying to prevent double-clicks
        self.resolve_btn.config(state="disabled", text="⏳ Querying...")
        self.status_var.set("Querying DNS servers... please wait.")
        self.root.update_idletasks()   # Refresh UI immediately

        # Run queries
        results = run_all_queries(domain, record_type)

        # Display results in the text box
        self._display_results(domain, record_type, results)

        # Find fastest server (among successful queries)
        successful = [r for r in results if r["success"]]
        if successful:
            fastest = min(successful, key=lambda r: r["response_time_ms"])
            self.status_var.set(
                f"✅  Fastest server: {fastest['server_name']} ({fastest['server_ip']})  "
                f"—  {fastest['response_time_ms']} ms"
            )
        else:
            self.status_var.set("⚠️  All queries failed. Check domain name or network connection.")

        # Save log
        try:
            save_log(domain, record_type, results)
        except Exception as e:
            self._write_output(f"\n[LOG ERROR] Could not save log: {e}\n")

        # Save and enable graph button
        try:
            graph_saved = save_graph(results)
            if graph_saved:
                self.graph_btn.config(state="normal")
        except Exception as e:
            self._write_output(f"\n[GRAPH ERROR] Could not save graph: {e}\n")

        # Re-enable resolve button
        self.resolve_btn.config(state="normal", text="▶  Resolve")

    def _display_results(self, domain, record_type, results):
        """Format and print query results into the output text area."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append("=" * 58)
        lines.append(f"  Query Time : {timestamp}")
        lines.append(f"  Domain     : {domain}")
        lines.append(f"  Record Type: {record_type}")
        lines.append("=" * 58)

        for r in results:
            lines.append(f"\n┌─ {r['server_name']}  [{r['server_ip']}]")
            if r["success"]:
                for rec in r["records"]:
                    lines.append(f"│  Record      : {rec}")
                lines.append(f"│  TTL         : {r['ttl']} seconds")
                lines.append(f"└  Response    : {r['response_time_ms']} ms")
            else:
                lines.append(f"└  ⚠ Error     : {r['error']}")

        lines.append("\n")   # Spacer between queries

        self._write_output("\n".join(lines))

    def _write_output(self, text):
        """Append text to the output box (handles read-only state)."""
        self.output_box.config(state="normal")
        self.output_box.insert("end", text)
        self.output_box.see("end")           # Auto-scroll to bottom
        self.output_box.config(state="disabled")

    def _clear_output(self):
        """Clear the output text area and reset the status label."""
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.config(state="disabled")
        self.status_var.set("Output cleared. Enter a domain and click Resolve.")
        self.graph_btn.config(state="disabled")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = DNSApp(root)
    root.mainloop()