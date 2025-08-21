

from lib.pdftoimg import pdf_to_images


imgs = pdf_to_images("./assets/invoice.pdf", zoom=2.0, threshold=120, printer_width=576)
print("pages:", len(imgs))
imgs[0].show()          # open first page in your OS viewer
