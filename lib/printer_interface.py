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
    # Open network printer (assumes Network class available)
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
    # Open USB printer (assumes Usb class available)
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







