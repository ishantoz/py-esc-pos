# POS Printer Bridge

A robust Flask-based bridge application that enables communication between web applications and thermal printers (ESPOS and TSPL) via USB and network connections. This bridge supports PDF printing, barcode generation, and provides a RESTful API for seamless integration.

## Features

- **Multi-Protocol Support**: ESPOS (ESC/POS) and TSPL printer protocols
- **Connection Types**: USB and Network (Ethernet/WiFi) printer connections
- **File Formats**: PDF to thermal printer conversion with image optimization
- **Barcode Printing**: Generate and print barcodes using TSPL commands
- **Queue Management**: Built-in print job queue with retry mechanisms
- **RESTful API**: HTTP endpoints for easy integration
- **Cross-Platform**: Windows, macOS, and Linux support
- **SSL Support**: Secure HTTPS communication

## System Requirements

### Operating Systems
- **Windows 10/11** (64-bit recommended)
- **macOS 10.14+**
- **Linux** (Ubuntu 18.04+, CentOS 7+, etc.)

### Hardware Requirements
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: 100MB free space
- **USB Ports**: For USB printer connections
- **Network**: For network printer connections

### Software Dependencies
- **Python 3.13+**
- **pip** or **uv** package manager
- **Git** (for cloning the repository)

## Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/ishantoz/py-esc-pos.git
cd py-esc-pos
```

### 2. Python Environment Setup

#### Option A: Using uv (Recommended)
```bash
# Install uv if not already installed
pip install uv

# Create virtual environment and install dependencies
uv sync
```

#### Option B: Using pip
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Operating System Specific Setup

#### Windows Setup

**USB Driver Installation (Required for USB printers):**

1. **Download Zadig**: Download [Zadig](https://zadig.akeo.ie/) from the official website
2. **Install USB Drivers**:
   - Connect your USB thermal printer
   - Run Zadig as Administrator
   - Select your printer from the device list
   - Choose either "libusbK" or "WinUSB" as the driver
   - Click "Install Driver" or "Replace Driver"

**Note**: Both libusbK and WinUSB drivers can work for USB thermal printers. If one doesn't work, try the other. The choice depends on your specific printer model and how the application communicates with it.

**Troubleshooting USB Issues**:

**Using uv**:
```bash
# Check USB device recognition
uv run -c "import usb.core; print([f'VID:{d.idVendor:04x} PID:{d.idProduct:04x}' for d in usb.core.find(find_all=True)])"
```

**Using pip/venv**:
```bash
# Check USB device recognition
python -c "import usb.core; print([f'VID:{d.idVendor:04x} PID:{d.idProduct:04x}' for d in usb.core.find(find_all=True)])"
```

#### macOS Setup

**USB Driver Installation**:
```bash
# Install libusb via Homebrew
brew install libusb

# Grant USB permissions to Terminal/IDE
# System Preferences > Security & Privacy > Privacy > USB
```

**Troubleshooting**:
```bash
# Check USB permissions
ls -la /dev/usb*
# If no devices found, check System Integrity Protection (SIP) status
csrutil status
```

#### Linux Setup

**Ubuntu/Debian**:
```bash
# Install system dependencies
sudo apt update
sudo apt install libusb-1.0-0-dev libudev-dev

# Add udev rules for USB access
sudo nano /etc/udev/rules.d/99-usb-thermal.rules
```

Add this content to the udev rules file:
```
SUBSYSTEM=="usb", ATTRS{idVendor}=="[YOUR_VENDOR_ID]", ATTRS{idProduct}=="[YOUR_PRODUCT_ID]", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="[YOUR_VENDOR_ID]", ATTRS{idProduct}=="[YOUR_PRODUCT_ID]", GROUP="dialout"
```

**CentOS/RHEL**:
```bash
# Install system dependencies
sudo yum install libusb1-devel systemd-devel

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 4. SSL Certificate Setup

**Generate Self-Signed Certificates**:
```bash
# Create certs directory
mkdir certs

# Generate private key
openssl genrsa -out certs/key.pem 2048

# Generate certificate
openssl req -new -x509 -key certs/key.pem -out certs/cert.pem -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**Windows (using Git Bash or WSL)**:
```bash
# Install OpenSSL if not available
# Download from: https://slproweb.com/products/Win32OpenSSL.html

# Generate certificates using the same commands as above
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:
```bash
# Server Configuration
POS_PRINTER_BRIDGE_PORT=5000
FLASK_ENV=production

# Database Configuration
DB_PATH = "data/db/data.db"
PDF_DIR = "data/pdf"
POS_PDF_JOB_DIR = f"{PDF_DIR}/esc-pos-jobs"

# SSL Configuration
SSL_CERT_PATH=certs/cert.pem
SSL_KEY_PATH=certs/key.pem
```

### Printer Configuration

**USB Printer Settings**:
```json
{
  "connection_type": "usb",
  "usb_vendor_id": "0x0483",
  "usb_product_id": "0x5740",
  "usb_interface": 0,
  "printer_width": 576,
  "threshold": 160,
  "feed_lines": 1,
  "zoom": 2.0
}
```

**Network Printer Settings**:
```json
{
  "connection_type": "network",
  "host": "192.168.1.100",
  "port": 9100,
  "printer_width": 576,
  "threshold": 100,
  "feed_lines": 1,
  "zoom": 2.0
}
```

## Usage

### 1. Running the Application

**Development Mode**:

**Option A: Using uv (Recommended)**:
```bash
# Run the application directly with uv
uv run main.py
```

**Option B: Using pip/venv**:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run the application
python main.py
```

**Production Mode**:

**Option A: Using uv**:
```bash
# Build executable
uv run build.py

# Run the built executable
./release/v1.0.0/POS Printer Bridge.exe  # Windows
./release/v1.0.0/POS Printer Bridge       # macOS/Linux
```

**Option B: Using pip/venv**:
```bash
# Build executable
python build.py

# Run the built executable
./release/v1.0.0/POS Printer Bridge.exe  # Windows
./release/v1.0.0/POS Printer Bridge       # macOS/Linux
```

### 2. API Endpoints

#### Health Check
```bash
GET /verify/status
```

#### Test ESPOS Connection
```bash
POST /verify/espos-connection
Content-Type: application/json

{
  "connection_type": "usb",
  "usb_vendor_id": "0x0483",
  "usb_product_id": "0x5740",
  "usb_interface": 0
}
```

#### Print PDF
```bash
POST /print/eos-pos-pdf
Content-Type: multipart/form-data

file: [PDF_FILE]
connection_type: usb
usb_vendor_id: 0x0483
usb_product_id: 0x5740
printer_width: 576
threshold: 160
feed_lines: 1
zoom: 2.0
```

#### Print Barcode (TSPL)
```bash
POST /print/tspl-barcode
Content-Type: application/json

{
  "connection_type": "usb",
  "usb_vendor_id": "0x0483",
  "usb_product_id": "0x5740",
  "sizeX": 50,
  "sizeY": 30,
  "barcodeData": "123456789",
  "barcodeHeight": 20,
  "printCount": 1
}
```

### 3. Integration Examples

**JavaScript/Node.js**:
```javascript
const FormData = require('form-data');
const fs = require('fs');

const form = new FormData();
form.append('file', fs.createReadStream('receipt.pdf'));
form.append('connection_type', 'usb');
form.append('usb_vendor_id', '0x0483');
form.append('usb_product_id', '0x5740');

fetch('https://localhost:5000/print/eos-pos-pdf', {
  method: 'POST',
  body: form
});
```

**Python**:
```python
import requests

files = {'file': open('receipt.pdf', 'rb')}
data = {
    'connection_type': 'usb',
    'usb_vendor_id': '0x0483',
    'usb_product_id': '0x5740',
    'printer_width': 576,
    'threshold': 160
}

response = requests.post(
    'https://localhost:5000/print/eos-pos-pdf',
    files=files,
    data=data,
    verify=False  # For self-signed certificates
)
```

**cURL**:
```bash
curl -X POST \
  -F "file=@receipt.pdf" \
  -F "connection_type=usb" \
  -F "usb_vendor_id=0x0483" \
  -F "usb_product_id=0x5740" \
  -F "printer_width=576" \
  -F "threshold=160" \
  https://localhost:5000/print/eos-pos-pdf
```

## Building and Distribution

### Building Executable

```bash
# Run the build script
python build.py
```

The build process will:
1. Create a PyInstaller executable
2. Bundle all dependencies
3. Include the `certs` folder
4. Output to `release/v1.0.0/Mohajon POS.exe`

### Build Configuration

Edit `build.py` to customize:
- Application version
- Release path
- Application name
- Icon file

## Troubleshooting

### Common Issues

**USB Device Not Found**:

**Using uv**:
```bash
# Check device recognition
uv run -c "import usb.core; print([f'VID:{d.idVendor:04x} PID:{d.idProduct:04x}' for d in usb.core.find(find_all=True)])"
```

**Using pip/venv**:
```bash
# Check device recognition
python -c "import usb.core; print([f'VID:{d.idVendor:04x} PID:{d.idProduct:04x}' for d in usb.core.find(find_all=True)])"
```

**Verify driver installation**:
- **Windows**: Check Device Manager
- **macOS**: Check System Information > USB
- **Linux**: Check lsusb command

**Permission Denied (Linux/macOS)**:
```bash
# Add user to dialout group (Linux)
sudo usermod -a -G dialout $USER

# Grant USB permissions (macOS)
# System Preferences > Security & Privacy > Privacy > USB
```

**SSL Certificate Errors**:
```bash
# Regenerate certificates
openssl genrsa -out certs/key.pem 2048
openssl req -new -x509 -key certs/key.pem -out certs/cert.pem -days 365
```

**Print Job Stuck in Queue**:
```bash
# Check database
sqlite3 print_queue.db "SELECT * FROM print_jobs WHERE status='pending';"

# Clear stuck jobs
sqlite3 print_queue.db "DELETE FROM print_jobs WHERE status='failed';"
```

### Debug Mode

Enable debug logging by setting environment variables:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Log Files

Check application logs for detailed error information:
- **Windows**: Check console output
- **macOS/Linux**: Check system logs or console output

## Development

### Project Structure
```
py-esc-pos/
├── lib/                    # Core library modules
│   ├── printer.py         # Printer interface
│   ├── printer_interface.py # Connection management
│   ├── pdftoimg.py       # PDF to image conversion
│   └── tspl.py           # TSPL protocol support
├── main.py                # Main Flask application
├── build.py               # Build script
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
├── certs/                 # SSL certificates
├── print_jobs/           # Temporary PDF storage
└── README.md             # This file
```

### Adding New Printer Protocols

1. Create a new module in `lib/`
2. Implement the required interface methods
3. Add new API endpoints in `main.py`
4. Update the build configuration if needed

### Testing

**Option A: Using uv**:
```bash
# Run basic tests
uv run test.py

# Test USB connection
uv run -c "from lib.tspl import check_printer_usb_connection; print(check_printer_usb_connection(0x0483, 0x5740))"

# Test network connection
uv run -c "from lib.tspl import check_printer_network_connection; print(check_printer_network_connection('192.168.1.100', 9100))"
```

**Option B: Using pip/venv**:
```bash
# Run basic tests
python test.py

# Test USB connection
python -c "from lib.tspl import check_printer_usb_connection; print(check_printer_usb_connection(0x0483, 0x5740))"

# Test network connection
python -c "from lib.tspl import check_printer_network_connection; print(check_printer_network_connection('192.168.1.100', 9100))"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation
- Test with the provided examples

## Changelog

### Version 1.0.0
- Initial release
- ESPOS and TSPL protocol support
- USB and Network printer connections
- PDF printing capabilities
- Barcode generation
- Print job queue management
- RESTful API
- SSL support
- Cross-platform compatibility

---

**Note**: This application requires proper USB driver installation on Windows systems. Use Zadig or similar tools to install the appropriate drivers for your thermal printer.
