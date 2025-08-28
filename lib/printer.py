from escpos.printer import Network, Usb
import io
import time
from lib.pdftoimg import pdf_to_images

ESC_INIT = b"\x1b@"
ESC_FEED_N = lambda n: b"\x1b\x64" + bytes([n])
ESC_ALIGN_L = b"\x1ba\x00"
CUT_FULL = b"\x1dV\x00"
CUT_PARTIAL = b"\x1dV\x01"

extra_feed_lines = 5

def print_pdf_on_thermal_printer(
    pdf_path: str,
    zoom: float = 2.0,
    printer_width: int = 576,
    threshold: int = 130,
    feed_lines: int = 1,
    pre_cut_min_lines: int = 6,
    printer: Network | Usb = None,
) -> None: 
    if printer is None:
        raise ValueError("Printer is required")

    images = pdf_to_images(
        pdf_path=pdf_path,
        zoom=zoom,
        threshold=threshold,
        printer_width=printer_width,
        crop=True,
        pad_pixels=None,
        blur_radius=0.5,
        contrast=1.3,
        binarize=True,
    )
  
    for img in images:
        printer._raw(ESC_INIT)
        printer._raw(ESC_ALIGN_L)

        with io.BytesIO() as buf:
            img.save(buf, format="PNG")
            printer.image(io.BytesIO(buf.getvalue()))

        pre_cut_lines = max(feed_lines + extra_feed_lines, pre_cut_min_lines + round(extra_feed_lines/2))
        printer._raw(ESC_FEED_N(pre_cut_lines))
        
        try:
            printer._raw(CUT_FULL)
        except Exception:
            try:
                printer.cut()
            except Exception:
                try:
                    printer._raw(CUT_PARTIAL)
                except Exception:
                    pass