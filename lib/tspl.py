import time
import usb.core
import socket

def build_barcode_tspl(sizeX, sizeY, gapLength, dir, topText, topTextStart, barcodeStart, barcodeData, printCount, barcodeHeight):
    heightDots = sizeY * 8
    textHeight = 12
    spacing = 10
    totalBlock = textHeight + barcodeHeight + spacing
    yOffset = (heightDots - totalBlock) // 2

    tspl = ""
    tspl += f"SIZE {sizeX} mm, {sizeY} mm\r\n"

    if gapLength > 0:
        tspl += f"GAP {gapLength} mm, 0 mm\r\n"

    tspl += f"DIRECTION {dir}\r\n"
    tspl += "CLS\r\n"
    tspl += "SET PRINTER DT\r\n"

    tspl += f'TEXT {topTextStart},{yOffset},"2",0,1,1,"{topText}"\r\n'
    tspl += f'BARCODE {barcodeStart},{yOffset+textHeight+spacing},"128",{barcodeHeight},1,0,2,2,"{barcodeData}"\r\n'
    tspl += f"PRINT {printCount},1\r\n"
    tspl += "CUT\r\n"

    return tspl

def check_printer_usb_connection(vid, pid):
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if dev is None:
        raise ValueError("Printer not found")
    return dev

def check_printer_network_connection(printer_ip, printer_port=9100, timeout=3):
    try:
        s = socket.create_connection((printer_ip, printer_port), timeout=timeout)
        return True
    except (socket.timeout, socket.error) as e:
        s.close()
        return False


def print_barcode_tspl(tspl, dev):
    data = tspl.encode("utf-8")
    dev.write(1, data)


def print_barcode_tspl_network(tspl, sock, verbose=False):
    try:
        data = tspl.encode("utf-8")
        sock.sendall(data)
        if verbose:
            print("[INFO] TSPL data sent successfully.")
        return True
    except socket.error as e:
        if verbose:
            print(f"[ERROR] Failed to send TSPL data: {e}")
        return False


def print_dummy_tspl(dev):
    tspl = (
        "SIZE 50 mm, 50 mm\r\n"
        "CLS\r\n"
        "TEXT 10,10,1,0,1,1,\"Hello, World!\"\r\n"
        "PRINT 1,1\r\n"
        "CUT\r\n"                 
    )

    data = tspl.encode("utf-8")
    dev.write(1, data)