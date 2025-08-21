# py-esc-pos

**Low-level ESC/POS printer control with raw command access and PDF-to-thermal printing**

A Python library for developers who need granular control over ESC/POS thermal printers. Send raw commands, handle PDF printing with custom image processing, and manage both network and USB printer connections.

## 🎯 What This Is

- **Raw ESC/POS command access** - Send byte-level commands directly to printers
- **PDF-to-thermal conversion** - Convert PDFs to optimized thermal printer images
- **Network & USB support** - Connect via TCP/IP or USB with vendor/product ID control
- **Image preprocessing pipeline** - Customizable threshold, contrast, blur, and binarization
- **Queue management** - REST API for print job queuing and status tracking
- **Low-level printer control** - Direct access to printer._raw() for custom commands

## 🚀 Quick Start

### Installation

```bash
# From source
git clone <repo>
cd py-esc-pos

# Option 1: Using uv (recommended if available)
uv sync

# Option 2: Using pip
pip install -e .

# Option 3: Install dependencies directly
pip install -r requirements.txt
```

**Note**: `uv sync` is the fastest option and will automatically create a virtual environment with all dependencies. If you don't have `uv` installed, you can install it with `pip install uv` or visit [uv.pm](https://uv.pm).

### OS-Specific Requirements

**⚠️ USB printer access requires different setup on each operating system**

#### Quick Setup Checklist

**Windows:**
- [ ] Run as Administrator
- [ ] Install libusb drivers with Zadig
- [ ] Replace original printer drivers
- [ ] Check Device Manager for conflicts

**Linux:**
- [ ] Add user to `dialout` group
- [ ] Log out and back in
- [ ] Check USB permissions with `lsusb`
- [ ] Verify udev rules if needed

**macOS:**
- [ ] Grant USB access to Terminal/IDE
- [ ] Check System Preferences → Security & Privacy → USB
- [ ] Ensure Terminal.app has USB permissions
- [ ] Check for SIP restrictions

#### Windows
- **Replace original printer drivers with libusb**: Use Zadig (included in project) to install libusb-win32 or WinUSB drivers
- **Run as Administrator**: Required for USB device access
- **Driver replacement process**:
  1. Connect your USB printer
  2. Run `zadig-2.9.exe` as Administrator
  3. Select your printer from the dropdown
  4. Choose "libusb-win32" or "WinUSB" driver
  5. Click "Replace Driver"

#### Linux
- **USB permissions**: Add your user to the `dialout` group or create udev rules
- **Group setup**:
  ```bash
  sudo usermod -a -G dialout $USER
  # Log out and back in, or run: newgrp dialout
  ```
- **Udev rules** (alternative): Create `/etc/udev/rules.d/99-printer.rules`:
  ```bash
  SUBSYSTEM=="usb", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", MODE="0666"
  # Replace xxxx/yyyy with your printer's vendor/product IDs
  ```

#### macOS
- **USB permissions**: Grant terminal/IDE access to USB devices in System Preferences
- **Security settings**: Go to System Preferences → Security & Privacy → Privacy → USB
- **Terminal access**: Add Terminal.app or your IDE to the USB access list
- **SIP considerations**: System Integrity Protection may require additional setup for some USB devices

### Basic Usage

```python
from lib.printer_interface import print_pdf_on_thermal_network

# Print PDF on network printer
print_pdf_on_thermal_network(
    pdf_path="invoice.pdf",
    printer_ip="192.168.1.100",
    printer_port=9100,
    printer_width=576,  # 80mm thermal printer
    zoom=2.0,          # Scale factor for better halftone conversion
    threshold=130,      # Binarization threshold (0-255)
    feed_lines=3        # Lines to feed before cutting
)
```

### USB Printer

```python
from lib.printer_interface import print_pdf_on_thermal_usb

# Print PDF on USB printer
print_pdf_on_thermal_usb(
    pdf_path="receipt.pdf",
    usb_vendor_id=0x0483,    # Find with lsusb or device manager
    usb_product_id=0x5740,
    usb_interface=0,
    printer_width=384          # 58mm thermal printer
)
```

## 🔧 Raw ESC/POS Commands

Access the printer at the byte level for maximum control:

```python
from lib.printer import ESC_INIT, ESC_FEED_N, CUT_FULL

# Initialize printer
printer._raw(ESC_INIT)

# Feed 5 lines
printer._raw(ESC_FEED_N(5))

# Full cut
printer._raw(CUT_FULL)
```

### Available Raw Commands

```python
ESC_INIT = b"\x1b@"                    # Initialize printer
ESC_FEED_N = lambda n: b"\x1b\x64" + bytes([n])  # Feed n lines
ESC_ALIGN_L = b"\x1ba\x00"             # Left align
CUT_FULL = b"\x1dV\x00"                # Full cut
CUT_PARTIAL = b"\x1dV\x01"             # Partial cut
```

## 🖨️ PDF Processing Pipeline

The PDF-to-thermal conversion includes several configurable steps:

```python
from lib.pdftoimg import pdf_to_images

images = pdf_to_images(
    pdf_path="document.pdf",
    zoom=2.0,              # Render scale (2.0 recommended)
    threshold=130,          # Binarization threshold
    printer_width=576,      # Target width in pixels
    crop=True,              # Auto-crop empty margins
    pad_pixels=5,          # Padding around content
    blur_radius=0.4,       # Gaussian blur for halftone
    contrast=1.3,          # Contrast enhancement
    binarize=True,          # Convert to black/white
    max_pages=None          # Limit pages to process
)
```

### Image Processing Steps

1. **PDF Rendering** - High-resolution rendering with PyMuPDF
2. **Auto-cropping** - Remove empty margins automatically
3. **Preprocessing** - Blur, contrast enhancement
4. **Resizing** - Scale to printer width while preserving aspect ratio
5. **Binarization** - Convert to black/white for thermal printing
6. **Width enforcement** - Ensure exact printer width match

## 🌐 REST API

Run the Flask server for print job queuing:

```bash
python main.py
```

### Endpoints

- `POST /print-pdf` - Queue a PDF for printing
- `GET /hello` - Health check
- Database-backed job queue with retry logic

### Example API Usage

```bash
# Network printer
curl -X POST http://localhost:5000/print-pdf \
  -F "file=@invoice.pdf" \
  -F "connection_type=network" \
  -F "host=192.168.1.100" \
  -F "port=9100" \
  -F "printer_width=576" \
  -F "threshold=130"

# USB printer
curl -X POST http://localhost:5000/print-pdf \
  -F "file=@receipt.pdf" \
  -F "connection_type=usb" \
  -F "usb_vendor_id=0x0483" \
  -F "usb_product_id=0x5740" \
  -F "printer_width=384"
```

## 🛠️ Advanced Usage

### Custom Printer Commands

```python
from lib.printer_interface import print_pdf_on_thermal_network

# Get printer instance for custom commands
printer = Network("192.168.1.100", 9100)

try:
    # Custom initialization
    printer._raw(b"\x1b@")  # Initialize
    printer._raw(b"\x1b\x61\x01")  # Center align
    
    # Your custom printing logic here
    
    # Custom feed and cut
    printer._raw(b"\x1b\x64\x05")  # Feed 5 lines
    printer._raw(b"\x1dV\x00")     # Full cut
    
finally:
    printer.close()
```

### Image Preview

```python
from lib.pdftoimg import preview_pdf_images

# Generate preview images
image_paths = preview_pdf_images(
    pdf_path="document.pdf",
    out_dir="previews",
    show=True,
    zoom=2.0,
    threshold=130
)
```

## 📊 Printer Specifications

### Common Thermal Printer Widths

- **58mm**: 384 pixels (48 bytes)
- **80mm**: 576 pixels (72 bytes)
- **112mm**: 832 pixels (104 bytes)

### ESC/POS Command Reference

| Command | Hex | Description |
|---------|-----|-------------|
| ESC @ | 1B 40 | Initialize printer |
| ESC d n | 1B 64 n | Feed n lines |
| ESC a n | 1B 61 n | Alignment (0=left, 1=center, 2=right) |
| GS V n | 1D 56 n | Cut (0=full, 1=partial) |

## 🔍 Troubleshooting

### Finding USB Printer IDs

**Linux/macOS:**
```bash
lsusb
# Look for your printer vendor/product IDs
```

**Windows:**
```cmd
# Device Manager → USB controllers → Properties → Details → Hardware IDs
# Format: USB\VID_xxxx&PID_yyyy
```

### OS-Specific USB Issues

#### Windows USB Problems
- **"Access denied" errors**: Run as Administrator and ensure libusb drivers are installed
- **Printer not detected**: Check Device Manager for yellow warning triangles
- **Driver conflicts**: Original printer drivers may block libusb access
- **Solution**: Use Zadig to completely replace the driver

#### Linux USB Permission Issues
- **"Permission denied" errors**: User not in `dialout` group
- **"Device busy" errors**: Another process is using the USB device
- **"No such device"**: Check if udev rules are properly configured
- **Debug commands**:
  ```bash
  lsusb                    # List USB devices
  groups $USER            # Check user groups
  sudo dmesg | tail      # Check kernel messages
  ```

#### macOS USB Access Issues
- **"Operation not permitted"**: USB access not granted to terminal/IDE
- **"Device not found"**: Check System Preferences → Security & Privacy → USB
- **SIP blocking**: System Integrity Protection may prevent USB access
- **Terminal permissions**: Ensure Terminal.app has USB access in Privacy settings

### Network Printer Issues

- Ensure port 9100 is open (default ESC/POS port)
- Check firewall settings
- Verify printer IP address and network connectivity

### Image Quality Issues

- Increase `zoom` for better halftone conversion
- Adjust `threshold` for optimal black/white balance
- Use `blur_radius` to smooth halftones before binarization

## 📦 Dependencies

- **python-escpos** - ESC/POS printer communication
- **PyMuPDF** - PDF processing and rendering
- **Pillow** - Image manipulation and processing
- **Flask** - REST API server
- **pyusb** - USB device communication

### Included Tools

- **Zadig** (`zadig-2.9.zip`) - Windows USB driver replacement tool
- **PowerShell scripts** - Windows service installation and management
- **Shell scripts** - Linux/macOS setup helpers

## 🏗️ Architecture

```
lib/
├── printer_interface.py    # High-level printer functions
├── printer.py             # Core printing logic + raw commands
└── pdftoimg.py           # PDF-to-image conversion pipeline

main.py                    # Flask REST API server
```

## 🤝 Contributing

This project is designed for developers who need low-level printer control. Contributions welcome:

- Raw ESC/POS command additions
- Image processing improvements
- Printer driver support
- Performance optimizations

## 📄 License

[Add your license here]

## 🔗 Related Projects

- [python-escpos](https://github.com/python-escpos/python-escpos) - Base ESC/POS library
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF processing
- [python-thermal-printer](https://github.com/adafruit/Adafruit_CircuitPython_Thermal_Printer) - CircuitPython thermal printer library
