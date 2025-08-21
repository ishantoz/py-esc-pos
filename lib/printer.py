from escpos.printer import Network, Usb
import io
from lib.pdftoimg import pdf_to_images

# ESC/POS raw commands
ESC_INIT = b"\x1b@"                      # initialize printer (reset)
ESC_FEED_N = lambda n: b"\x1b\x64" + bytes([n])  # ESC d n -> feed n lines
ESC_ALIGN_L = b"\x1ba\x00"               # left align
CUT_FULL = b"\x1dV\x00"                  # GS V 0 -> full cut
CUT_PARTIAL = b"\x1dV\x01"               # GS V 1 -> partial cut (fallback)


def print_pdf_on_thermal_printer(
    pdf_path: str,
    zoom: float = 2.0,
    printer_width: int = 576,
    threshold: int = 130,
    feed_lines: int = 1,
    pre_cut_min_lines: int = 8,
    printer: Network | Usb = None,
) -> None: 
    if printer is None:
        raise ValueError("Printer is required")

    # Convert PDF to prepared images
    images = pdf_to_images(
        pdf_path=pdf_path,
        zoom=zoom,
        threshold=threshold,
        printer_width=printer_width,
        crop=True,
        pad_pixels=None,
        blur_radius=0.4,
        contrast=1.3,
        binarize=True,
    )
  
    for img in images:
        # 7) Send to printer
        printer._raw(ESC_INIT)
        printer._raw(ESC_ALIGN_L)

        with io.BytesIO() as buf:
            # save prepared PIL image as PNG and send via the printer library's image method
            img.save(buf, format="PNG")
            printer.image(io.BytesIO(buf.getvalue()))

        # ---- Improved feed + cut logic ----
        pre_cut_lines = max(feed_lines, pre_cut_min_lines)
        # send feed to physically move paper past cutter
        printer._raw(ESC_FEED_N(pre_cut_lines))

        # Try explicit full cut; fall back to library cut() or partial cut if necessary
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