import logging
import sys
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from flask import Flask, request, jsonify, redirect
import sqlite3, os, threading, time

from werkzeug.utils import secure_filename
from lib.path import resource_path
from lib.printer_interface import print_pdf_on_thermal_network, print_pdf_on_thermal_usb, verify_connection_espos_on_usb, verify_connection_espos_on_network
import uuid
from flask_cors import CORS
from lib.tspl import check_printer_usb_connection, check_printer_network_connection, build_barcode_tspl, print_barcode_tspl, print_barcode_tspl_network, print_dummy_tspl 
    
DB_PATH = "data/db/data.db"
PDF_DIR = "data/pdf"
POS_PDF_JOB_DIR = f"{PDF_DIR}/esc-pos-jobs"

MAX_RETRIES = 3

if not os.path.exists(DB_PATH):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR, exist_ok=True)

if not os.path.exists(POS_PDF_JOB_DIR):
    os.makedirs(POS_PDF_JOB_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

new_job_event = threading.Event()


def init_db():
    """
    Initialize or migrate the database to include retry columns.
    """
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS print_jobs (
              id               INTEGER PRIMARY KEY AUTOINCREMENT,
              file_path        TEXT    NOT NULL,
              connection_type  TEXT    NOT NULL CHECK(connection_type IN ('network','usb')),
              printer_ip       TEXT,
              printer_port     INTEGER,
              usb_vendor_id    INTEGER,
              usb_product_id   INTEGER,
              usb_interface    INTEGER DEFAULT 0,
              printer_width    INTEGER DEFAULT 576,
              threshold        INTEGER DEFAULT 100,
              feed_lines       INTEGER DEFAULT 1,
              zoom             REAL    DEFAULT 2.0,
              status           TEXT    DEFAULT 'pending',
              retry_count      INTEGER DEFAULT 0,
              last_error       TEXT,
              created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_status_created ON print_jobs(status, created_at);"
        )
        conn.commit()

@app.route("/verify/status", methods=["GET"])
def verify_status():
    return jsonify({"message": "POS Printer Bridge is running"}), 200
    
@app.route("/verify/espos-connection", methods=["POST"])
def verify_espos_connection():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400
    conn_type = data["connection_type"]
    if conn_type == "network":
        host = data["host"]
        port = data["port"]
        if not host or not port:
            return jsonify({"error": "Missing host or port"}), 400
        if verify_connection_espos_on_network(host, port):
            return jsonify({"message": "ESPOS connection verified"}), 200
        else:
            return jsonify({"error": "ESPOS connection failed"}), 400
    else:
        vid = data["usb_vendor_id"]
        pid = data["usb_product_id"]
        iface = data.get("usb_interface", 0)  
        if not vid or not pid:
            return jsonify({"error": "Missing USB vendor_id or product_id"}), 400
        try:
            usb_vendor_id = int(vid, 16)
            usb_product_id = int(pid, 16)
            usb_interface = int(iface)
            if verify_connection_espos_on_usb(usb_vendor_id, usb_product_id, usb_interface):
                return jsonify({"message": "ESPOS connection verified"}), 200
            else:
                return jsonify({"error": "ESPOS connection failed"}), 400
        except ValueError:
            return jsonify({"error": "Invalid USB IDs or interface"}), 400



@app.route("/print/eos-pos-pdf", methods=["POST"])
def queue_print():
    file = request.files.get("file")
    conn_type = request.form.get("connection_type")
    if not file or conn_type not in ("network", "usb"):
        return jsonify({"error": "Missing file or invalid connection_type"}), 400

    filename = secure_filename(file.filename)
    unique_id = uuid.uuid4().hex
    save_path = os.path.join(POS_PDF_JOB_DIR, f"{unique_id}_{filename}")
    file.save(save_path)

    printer_width = int(request.form.get("printer_width", 576))
    threshold = int(request.form.get("threshold", 100))
    feed_lines = int(request.form.get("feed_lines", 1))
    zoom = float(request.form.get("zoom", 2.0))
    
    host = port = usb_vendor_id = usb_product_id = usb_interface = None

    if conn_type == "network":
        host = request.form.get("host")
        port = request.form.get("port")
        if not host or not port:
            return jsonify({"error": "Missing host or port"}), 400
        try:
            port = int(port)
        except ValueError:
            return jsonify({"error": "Invalid port"}), 400
    else:
        vid = request.form.get("usb_vendor_id")
        pid = request.form.get("usb_product_id")
        iface = request.form.get("usb_interface", "0")
        if not vid or not pid:
            return jsonify({"error": "Missing USB vendor_id or product_id"}), 400
        try:
            usb_vendor_id = int(vid, 16)
            usb_product_id = int(pid, 16)
            usb_interface = int(iface)
        except ValueError:
            return jsonify({"error": "Invalid USB IDs or interface"}), 400

    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        conn.execute(
            """
            INSERT INTO print_jobs (
                file_path,
                connection_type,
                printer_ip, printer_port,
                usb_vendor_id, usb_product_id, usb_interface,
                printer_width, threshold, feed_lines, zoom
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                save_path,
                conn_type,
                host,
                port,
                usb_vendor_id,
                usb_product_id,
                usb_interface,
                printer_width,
                threshold,
                feed_lines,
                zoom,
            ),
        )
        conn.commit()

    new_job_event.set()
    return jsonify({"message": "Print job queued"}), 202



@app.route("/verify/tspl-connection", methods=["POST"])
def verify_tspl_connection():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        required_fields = ["vid", "pid"]
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        vid = hex(data["vid"])
        pid = hex(data["pid"])

        dev = check_printer_usb_connection(vid, pid)
        if dev is None:
            return jsonify({"error": "Printer not found"}), 400
        print_dummy_tspl(dev)
        return jsonify({"message": "Printer found"}), 200
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid data types in JSON"}), 400


@app.route("/print/tspl-barcode", methods=["POST"])
def print_barcode_label():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    connection_type = str(data.get("connection_type", "usb")).lower()
    if connection_type not in ("usb", "network"):
        return jsonify({"error": "Invalid connection type. Use 'usb' or 'network'."}), 400

    base_required = ["sizeX", "sizeY", "barcodeData", "barcodeHeight"]
    if connection_type == "usb":
        required = base_required + ["usb_vendor_id", "usb_product_id"]
    else:  # network
        required = base_required + ["host", "port"]

    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        sizeX = int(data["sizeX"])
        sizeY = int(data["sizeY"])
        barcodeData = str(data["barcodeData"])
        barcodeHeight = int(data["barcodeHeight"])

        gapLength = int(data.get("gapLength", 0))
        direction = int(data.get("dir", 0))
        topText = str(data.get("topText", ""))
        topTextStart = int(data.get("topTextStart", 15))
        printCount = int(data.get("printCount", 1)) or 1
        barcodeStart = int(data.get("barcodeStart", 0))

        tspl = build_barcode_tspl(
            sizeX, sizeY, gapLength, direction,
            topText, topTextStart, barcodeStart,
            barcodeData, printCount, barcodeHeight
        )

        if connection_type == "usb":
            usb_vendor_id = int(data["usb_vendor_id"], 16)
            usb_product_id = int(data["usb_product_id"], 16)
            
            dev = check_printer_usb_connection(usb_vendor_id, usb_product_id)
            if dev is None:
                return jsonify({"error": "USB printer not found"}), 400

            print_barcode_tspl(tspl, dev)
            return jsonify({"message": "Barcode label printed via USB"}), 200

        else:  # network
            host = str(data["host"])
            port = int(data.get("port", 9100))
            try:
                sock = check_printer_network_connection(host, port)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            try:
                ok = print_barcode_tspl_network(tspl, sock)
                if not ok:
                    return jsonify({"error": "Failed to send TSPL to network printer"}), 500
                return jsonify({"message": "Barcode label printed via network"}), 200
            finally:
                try:
                    sock.close()
                except Exception:
                    pass

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid data: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500
    finally:
        if connection_type == "network":
            sock.close()


def printer_worker():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    while True:
        new_job_event.wait(timeout=0.2)
        new_job_event.clear()

        while True:
            job = conn.execute(
                """
                SELECT * FROM print_jobs
                WHERE
                  (status='pending')
                  OR
                  (status='failed' AND retry_count < ?)
                ORDER BY created_at
                LIMIT 1
                """, (MAX_RETRIES,)
            ).fetchone()
            if not job:
                break

            job_id = job["id"]
            conn.execute(
                "UPDATE print_jobs SET status='printing' WHERE id=?", (job_id,)
            )
            conn.commit()
            try:
                if job["connection_type"] == "network":
                    print_pdf_on_thermal_network(
                        pdf_path=job["file_path"],
                        printer_ip=job["printer_ip"],
                        printer_port=job["printer_port"],
                        printer_width=job["printer_width"],
                        threshold=job["threshold"],
                        feed_lines=job["feed_lines"],
                        zoom=job["zoom"],
                    )
                else:
                    print_pdf_on_thermal_usb(
                        pdf_path=job["file_path"],
                        usb_vendor_id=job["usb_vendor_id"],
                        usb_product_id=job["usb_product_id"],
                        usb_interface=job["usb_interface"],
                        printer_width=job["printer_width"],
                        threshold=job["threshold"],
                        feed_lines=job["feed_lines"],
                        zoom=job["zoom"],
                    )

                try:
                    os.remove(job["file_path"])
                except OSError:
                    print(f"[WARN] Could not delete file {job['file_path']}")
                conn.execute("DELETE FROM print_jobs WHERE id=?", (job_id,))
                conn.commit()

            except Exception as e:
                err = str(e)
                conn.execute(
                    """
                    UPDATE print_jobs
                       SET
                         status = CASE
                                    WHEN retry_count+1 < ? THEN 'pending'
                                    ELSE 'failed'
                                  END,
                         retry_count = retry_count + 1,
                         last_error = ?
                     WHERE id = ?
                    """, (MAX_RETRIES, err, job_id)
                )
                conn.commit()
                time.sleep(2)



class GuiConsole(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("POS Printer Bridge")
        self.geometry("700x500")

        # Set icon
        self.iconbitmap('app.ico')

        # Scrolled text for logs
        self.text_area = ScrolledText(self, state='disabled', bg='black', fg='white')
        self.text_area.pack(fill='both', expand=True)

        # Redirect stdout/stderr
        sys.stdout = self
        sys.stderr = self

        # Start server automatically
        threading.Thread(target=self.run_server, daemon=True).start()

    def write(self, message):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, message)
        self.text_area.yview(tk.END)
        self.text_area.config(state='disabled')

    def flush(self):
        pass  # Required for compatibility

    def run_server(self):
        print("Starting POS Printer Bridge server...")
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        init_db()
        threading.Thread(target=printer_worker, daemon=True).start()
        port = int(os.environ.get("POS_PRINTER_BRIDGE_PORT", 5000))
        print(f"Server started at https://localhost:{port}")
        app.run(
            debug=False,
            port=port,
            host="0.0.0.0",
            threaded=True,
            ssl_context=("certs/cert.pem", "certs/key.pem")
        )


if __name__ == "__main__":
    gui = GuiConsole()
    gui.mainloop()