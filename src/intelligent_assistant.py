import numpy as np
import pytesseract


def predict_text_from_images(image_list, progress, total_progress, update=lambda: None):
    char_blacklist = '''0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX{}Y;：Z#「’:_‘、,<>.-^\\'\\"'''
    tesseract_config = f'''--psm 10 -c tessedit_char_blacklist={char_blacklist} --tessdata-dir "./weights"'''
    output = ""

    for num, img in enumerate(image_list):
        img = np.asarray(img)
        try:
            prediction = pytesseract.image_to_string(img, lang="chi_tra", config=tesseract_config)[0]
        except pytesseract.pytesseract.TesseractError as error:
            print("\n\n Error: Need to install tesseract chi_tra. Refer to README.md to install.")
            print(error)
            return None

        if prediction == "\x0c":
            prediction = " "
        output += prediction

        new_progress = progress.get()/100 * total_progress
        progress.set(100*(new_progress+1)/total_progress)
        update()
    return output