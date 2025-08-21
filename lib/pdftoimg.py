import io
import os
from typing import List, Optional
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import fitz  # PyMuPDF


def pdf_to_images(
    pdf_path: str,
    zoom: float = 2.0,
    threshold: int = 130,
    printer_width: Optional[int] = None,
    crop: bool = True,
    pad_pixels: Optional[int] = None,
    blur_radius: float = 0.4,
    contrast: float = 1.3,
    binarize: bool = True,
    max_pages: Optional[int] = None,
) -> List[Image.Image]:
    """
    Convert PDF pages to PIL Images prepared for thermal printing.

    Returns a list of PIL.Image instances (mode '1' if binarize=True, else 'L').

    Args:
        pdf_path:         path to PDF
        zoom:             render scale (2.0 recommended for better halftone->b/w)
        threshold:        binarization threshold 0..255 (lower = darker)
        printer_width:    if set, resizes images to this width in pixels (preserve aspect)
        crop:             auto-crop empty margins (top/bottom/left/right)
        pad_pixels:       padding in pixels to keep around cropped content (default: ~1% of width)
        blur_radius:      gaussian blur radius (helps halftone->binarize)
        contrast:         multiplier for contrast enhancement
        binarize:         whether to convert to black/white (mode '1')
        max_pages:        stop after this many pages (None -> all)
    """
    doc = fitz.open(pdf_path)
    images: List[Image.Image] = []

    for i, page in enumerate(doc):
        if max_pages is not None and i >= max_pages:
            break

        # render page
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes(output="png"))).convert("L")  # grayscale

        # choose padding default relative to current image width if not provided
        if pad_pixels is None:
            pad_pixels = max(2, int((printer_width or img.width) * 0.01))

        # optional crop: find non-white bbox using threshold
        if crop:
            bw = img.point(lambda p: 0 if p < threshold else 255, mode="1")
            bbox = bw.getbbox()
            if bbox:
                left, upper, right, lower = bbox
                left = max(0, left - pad_pixels)
                upper = max(0, upper - pad_pixels)
                right = min(img.width, right + pad_pixels)
                lower = min(img.height, lower + pad_pixels)
                img = img.crop((left, upper, right, lower))
            # else: leave image as-is (blank page)

        # mild preprocessing
        if blur_radius and blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        if contrast and contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)

        # resize to printer width if requested
        if printer_width is not None and img.width != printer_width:
            new_h = max(1, int(img.height * (printer_width / img.width)))
            # resize in L (grayscale) before final binarize
            img = img.resize((printer_width, new_h), Image.LANCZOS)

        # final binarization (if desired)
        if binarize:
            img = img.point(lambda p: 0 if p < threshold else 255, mode="1")
            # ensure exact width (safety)
            if printer_width is not None and img.width != printer_width:
                img = img.resize((printer_width, img.height), Image.NEAREST)
        else:
            # keep as grayscale 'L'
            if printer_width is not None and img.width != printer_width:
                img = img.resize((printer_width, img.height), Image.LANCZOS)

        images.append(img)

    doc.close()
    return images


def preview_pdf_images(
    pdf_path: str,
    out_dir: Optional[str] = None,
    show: bool = True,
    **pdf_to_images_kwargs,
) -> List[str]:
    """
    Convert PDF -> images (via pdf_to_images) and either show them or save to disk.

    Returns list of file paths written (or empty list if show=True and nothing saved).
    """
    images = pdf_to_images(pdf_path, **pdf_to_images_kwargs)

    saved_paths: List[str] = []
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    for idx, img in enumerate(images):
        if show:
            # .show() uses the default image viewer; it spawns a process on many OSes.
            img.show(title=f"PDF page {idx + 1}")
        if out_dir:
            fname = os.path.join(out_dir, f"pdf_preview_page_{idx + 1}.png")
            # save binarized images as PNG for easy inspection
            img.save(fname, format="PNG")
            saved_paths.append(fname)

    return saved_paths
