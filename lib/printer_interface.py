from escpos.printer import Network, Usb
from lib.printer import print_pdf_on_thermal_printer


def print_pdf_on_thermal_network(
    pdf_path: str,
    printer_ip: str,
    printer_port: int = 9100,
    printer_width: int = 576,
    zoom: float = 2.0,
    feed_lines: int = 1,
    threshold: int = 130,
) -> None:
    printer = Network(printer_ip, printer_port)
    try:
        print_pdf_on_thermal_printer(
            pdf_path=pdf_path,
            printer=printer,
            zoom=zoom,
            printer_width=printer_width,
            threshold=threshold,
            feed_lines=feed_lines,
        )
    finally:
        printer.close()


def print_pdf_on_thermal_usb(
    pdf_path: str,
    usb_vendor_id: int,
    usb_product_id: int,
    usb_interface: int = 0,
    printer_width: int = 576,
    zoom: float = 2.0,
    feed_lines: int = 1,
    threshold: int = 160,
) -> None:
    printer = Usb(usb_vendor_id, usb_product_id, interface=usb_interface)
    try:
        print_pdf_on_thermal_printer(
            pdf_path=pdf_path,
            printer=printer,
            zoom=zoom,
            printer_width=printer_width,
            threshold=threshold,
            feed_lines=feed_lines,
        )
    finally:
        printer.close()


def verify_connection_espos_on_network(
    printer_ip: str,
    printer_port: int = 9100,
) -> bool:
    printer = Network(printer_ip, printer_port)
    try:
        text = f"Verify Success! \n"
        text += f"Network Connection Type: Network \n"
        text += f"Network IP: {printer_ip} \n"
        text += f"Network Port: {printer_port} \n"
        printer.text(text)
        printer.cut()
        return True
    except Exception as e:
        printer.close()
        return False
    finally:
        printer.close()

def verify_connection_espos_on_usb(
    usb_vendor_id: str,
    usb_product_id: str,
    usb_interface: int = 0,
) -> bool:
    printer = Usb(usb_vendor_id, usb_product_id, interface=usb_interface)
    try:
        text = f"Verify Success! \n"
        text += f"USB Connection Type: USB \n"
        text += f"USB Vendor ID: {hex(usb_vendor_id)} \n"
        text += f"USB Product ID: {hex(usb_product_id)} \n"
        text += f"USB Interface: {usb_interface} \n"
        printer.text(text)
        printer.cut()
        return True
    except Exception as e:
        printer.close()
        return False
    finally:
        printer.close()