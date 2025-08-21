from flask import Flask, request, jsonify
import sqlite3, os, threading, time
from lib.printer_interface import print_pdf_on_thermal_network, print_pdf_on_thermal_usb
import uuid
from flask_cors import CORS

DB_PATH = "print_queue.db"
PDF_DIR = "print_jobs"
MAX_RETRIES = 3
os.makedirs(PDF_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# Event to wake the printer worker immediately on new jobs
new_job_event = threading.Event()


def init_db():
    """
    Initialize or migrate the database to include retry columns.
    """
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        # Create table if not exists
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

@app.route("/hello", methods=["GET"])
def hello_api():
    return jsonify({"message": "HELLO FROM POS PRINTER BRIDGE"})

@app.route("/print-pdf", methods=["POST"])
def queue_print():
    file = request.files.get("file")
    conn_type = request.form.get("connection_type")
    if not file or conn_type not in ("network", "usb"):
        return jsonify({"error": "Missing file or invalid connection_type"}), 400

    # Save uploaded PDF
    filename = secure_filename(file.filename)
    unique_id = uuid.uuid4().hex
    save_path = os.path.join(PDF_DIR, f"{unique_id}_{filename}")
    file.save(save_path)

    # Shared print options
    printer_width = int(request.form.get("printer_width", 576))
    threshold = int(request.form.get("threshold", 100))
    feed_lines = int(request.form.get("feed_lines", 1))
    zoom = float(request.form.get("zoom", 2.0))

    # Connection-specific parameters
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


if __name__ == "__main__":
    init_db()
    threading.Thread(target=printer_worker, daemon=True).start()
    port = int(os.environ.get("POS_PRINTER_BRIDGE_PORT", 5000))
    app.run(
    debug=False,
    port=port,
    host="0.0.0.0",
    threaded=True,
    ssl_context=("certs/cert.pem", "certs/key.pem")
)
