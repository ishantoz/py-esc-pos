# import random
# import string
# import usb.core
# import usb.util

# def mm_to_dots(mm, dpi=203):
#     return int(round(mm * dpi / 25.4))

# # Replace with your printer's VID and PID
# VID = 0x0FE6
# PID = 0x8800

# # Find the device
# dev = usb.core.find(idVendor=VID, idProduct=PID)
# if dev is None:
#     raise ValueError("Printer not found")

# # Helper to build TSPL command string
# def build_tspl(sizeX, sizeY, gapLength, dir, topText, topTextStart, barcodeStart, barcodeData, printCount, barcodeHeight):
#     heightDots = sizeY * 8
#     textHeight = 12
#     spacing = 10
#     totalBlock = textHeight + barcodeHeight + spacing
#     yOffset = (heightDots - totalBlock) // 2

#     tspl = ""
#     tspl += f"SIZE {sizeX} mm, {sizeY} mm\r\n"

#     if gapLength > 0:
#         tspl += f"GAP {gapLength} mm, 0 mm\r\n"

#     tspl += f"DIRECTION {dir}\r\n"
#     tspl += "CLS\r\n"
#     tspl += "SET PRINTER DT\r\n"

#     tspl += f'TEXT {topTextStart},{yOffset},"2",0,1,1,"{topText}"\r\n'
#     tspl += f'BARCODE {barcodeStart},{yOffset+textHeight+spacing},"128",{barcodeHeight},1,0,2,2,"{barcodeData}"\r\n'
#     tspl += f"PRINT {printCount},1\r\n"
#     tspl += "CUT\r\n"

#     return tspl
    
# def generate_barcode(length=10):
#     # Uppercase alphabets and digits only
#     chars = string.ascii_uppercase + string.digits
#     # Generate random string
#     return ''.join(random.choice(chars) for _ in range(length))

# # Example values (adjust as needed)
# sizeX = 45   
# sizeY = 35     
# gapLength = 2
# dir = 0
# topText = "Hello USB"
# barcodeData = 'N86C76CD57C'
# printCount = 1
# barcodeHeight = 75
# topTextStart = 15
# barcodeStart = 3

# # Build TSPL
# tspl = build_tspl(sizeX, sizeY, gapLength,dir, topText, topTextStart, barcodeStart, barcodeData, printCount, barcodeHeight)

# # Send TSPL to printer
# data = tspl.encode("ascii")
# dev.write(1, data)   # 1 = OUT endpoint, may need to be changed


def mm_to_pixels(mm, dpi=203):
    """Convert millimeters to printer pixels/dots."""
    return int(round(mm * dpi / 25.4))


print(mm_to_pixels(70))