## test_script.py
# import 
from __future__ import annotations
from pathlib import Path
import pytesseract
from PIL import Image
from pix2tex.cli import LatexOCR

import base64
import mimetypes
from pathlib import Path

from openai import OpenAI
from src.core.config import agentic_env_vars

OCR_SUFFIXES = [
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    # ".bmp",
    # ".webp"
    ]


def run_image_text_conversion():
    folder = Path("/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/JLoviscach_Mathe_1/frames")
    # parsing_env_vars.data_dir / "images_ocr"
    # 
    f_paths = [f for f in folder.iterdir()
               if f.is_file()]
    print(f"Found {len(f_paths)} files in folder.")

    image_text_conversion(
                f_paths=f_paths[:2],
                # [Path(f"{folder}/20260313_073901.jpg")],
                mode="open_ai"
                ) # 


def validate_ocr_file(path: str | Path) -> Path:
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(path)

    if path.suffix.lower() not in OCR_SUFFIXES:
        raise ValueError(
            f"Unsupported OCR file type: {path.suffix}. "
            f"Supported: {sorted(OCR_SUFFIXES)}"
        )

    return path


def image_to_data_url(path: str | Path) -> str:
    path = Path(path)

    mime_type, _ = mimetypes.guess_type(path)
    if mime_type is None:
        raise ValueError(
            f"Could not determine MIME type for '{path.name}'."
        )

    image_b64 = base64.b64encode(
        path.read_bytes()
    ).decode("utf-8")

    return (
        f"data:{mime_type};base64,"
        f"{image_b64}"
    )


# OCR 
def image_text_conversion(
                    f_paths: list[Path],
                    mode: str
                    ) -> None:

    model = LatexOCR()
    for idx, path in enumerate(f_paths): 

        print(f"Start converting file #{idx}: '{path.name}' ")

        path = validate_ocr_file(path)
        # if path.suffix not in ALLOWED_OCR_SUFFIXES:
        #     print(f"[ERROR] File '{path.name}' is not suitable; wrong suffix\n")
        #     continue
        
        with Image.open(path) as img:
            print("Format:", img.format)
            print("Size:", img.size)
            print("Mode:", img.mode)

            match mode:
                case "tesseract": 
                    text = pytesseract.image_to_string(
                            img,
                            lang="deu",
                            )
                    
                case "pic2tex": 
                    text = model(img)

                case "open_ai":
                    text = analyze_math_image(path)

                case _:
                    print(f"[ERROR] Unknown mode: {mode}")

        print(text)
        print("-" * 80)


def analyze_math_image(
    path: str | Path,
    model: str = "gpt-5.6-terra",
) -> str:

    path = Path(path)

    client = OpenAI(api_key=agentic_env_vars.openai_api_key)

    prompt = """
Analyze the mathematical content visible in this image.

Tasks:
1. Transcribe all clearly readable mathematical expressions.
2. Return mathematical notation as LaTeX where possible.
3. Briefly describe the relationship between the expressions.
4. Distinguish visible information from inferred information.
5. Do not reconstruct or invent symbols, numbers, signs, or vector
   components that are not clearly visible.
6. If something is ambiguous, explicitly mark it as ambiguous.

Focus on mathematical content rather than general image description.
"""

    response = client.responses.create(
        model=model,
        input=[
            {
            "role": "user",
            "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": image_to_data_url(path),
                    },
                ],
            }
        ],
    )

    return response.output_text

"""
Reply openAI:
Start converting file #0: 'section_000_000_t175.08.png' 
Format: PNG
Size: (854, 480)
Mode: RGB
### Clearly visible mathematical expressions

\[
\begin{pmatrix}
1\\
2
\end{pmatrix}
\cdot
\begin{pmatrix}
3\\
4
\end{pmatrix}
=
1\cdot 3 + 2\cdot 4
\]

\[
= 3 + 8
\]

\[
= 11
\]

The label written beside this calculation is:

\[
\text{Skalarprodukt}
\]

---

\[
\begin{pmatrix}
1\\
2\\
3
\end{pmatrix}
\times
\begin{pmatrix}
4\\
3\\
2
\end{pmatrix}
=
\begin{pmatrix}
\ \\
\ \\
\ 
\end{pmatrix}
\]

The vector on the right is visibly empty; no components are written.

The label beside this expression is:

\[
\text{Vektorprodukt}
\]

---

### Relationship between the expressions

- The first expression demonstrates a **scalar product (dot product)** of two two-dimensional vectors:
  \[
  (1,2)\cdot(3,4)=1\cdot3+2\cdot4=11.
  \]
  Its result is a scalar.

- The second expression sets up a **vector product (cross product)** of two three-dimensional vectors:
  \[
  (1,2,3)\times(4,3,2).
  \]
  Its intended result is shown as a three-component column vector, but its entries are not visible/written.

### Visible vs. inferred information

**Visible:**
- The dot-product calculation and the result \(11\).
- The vectors \(\begin{pmatrix}1\\2\end{pmatrix}\), \(\begin{pmatrix}3\\4\end{pmatrix}\), \(\begin{pmatrix}1\\2\\3\end{pmatrix}\), and \(\begin{pmatrix}4\\3\\2\end{pmatrix}\).
- The labels “Skalarprodukt” and “Vektorprodukt.”
- An empty parenthesized three-component result area for the cross product.

**Not visible / not transcribed as a result:**
- The components of the cross-product result. Although they could be computed, they are not written in the image and are therefore not reconstructed here.
--------------------------------------------------------------------------------
Start converting file #1: 'section_000_001_t180.08.png' 
Format: PNG
Size: (854, 480)
Mode: RGB
### Clearly readable expressions

\[
\begin{pmatrix}
1\\
2
\end{pmatrix}
\cdot
\begin{pmatrix}
3\\
4
\end{pmatrix}
= 1\cdot 3 + 2\cdot 4
\]

\[
= 3+8
\]

\[
= 11
\]

Label:

\[
\text{Skalarprodukt}
\]

A second expression is shown:

\[
\begin{pmatrix}
1\\
2\\
3
\end{pmatrix}
\times
\begin{pmatrix}
4\\
\text{ambiguous}\\
2
\end{pmatrix}
=
\begin{pmatrix}
\;\;\\
\;\;\\
\;\;
\end{pmatrix}
\]

Label:

\[
\text{Vektorprodukt}
\]

### Relationship between the expressions

- The upper calculation demonstrates the **scalar product** (dot product) of two two-dimensional vectors:
  \[
  (1,2)\cdot(3,4)=11.
  \]
- The lower expression appears intended to demonstrate the **vector product** / cross product of two three-dimensional vectors. Its result vector is left blank.

### Ambiguities and limitations

- In the second vector of the lower expression, the middle component is not fully clear. It resembles \(3\), but it is not sufficiently unambiguous to transcribe as definitely \(3\).
- The components of the resulting cross-product vector are not written; the displayed column vector is empty.
- A red circular cursor/marker overlaps the blank result-vector area, but no mathematical symbol or component is clearly visible underneath it.
"""

# torch 2.13.0+cpu
# torchvision 0.28.0
# pix2tex 0.1.4
# timm 0.5.4


# PyTesseract:
#  python -m src.test_script
# Found 118 files in folder.
# Start converting file #0: 'section_000_000_t175.08.png' 
# (.(2) = Ener Ikalar -
# produrt

# Er] { Uli

# Start converting file #1: 'section_000_001_t180.08.png' 
# (() = HEHer Ikalar -
# produrt

# GE) \ ; Uhl

# Start converting file #2: 'section_000_002_t185.08.png' 
# (() = HEHer Ikalar -
# produrt

# X ) Uhl

# Start converting file #3: 'section_000_003_t190.08.png' 
# (() = Ener Ikalar -
# produrt

# ET ) one

# Start converting file #4: 'section_000_004_t195.08.png' 
# (() = ee Ikalar -
# produrt

# (3 x 2) r i Uhse produkt

# Start converting file #5: 'section_000_005_t200.08.png' 
# (.(2) = HE Ikalar -
# produrt

# (F x 2) n i Uhse produkt

# Start converting file #6: 'section_000_006_t205.08.png' 
# (.(2) = ee Ikalar -
# produrt

# Ch - Ups

# Start converting file #7: 'section_000_007_t210.08.png' 
# (2).(2) ee nn

# Fr 474)

# Start converting file #8: 'section_000_008_t215.08.png' 
# 2.2) = =N.3+2- er Skalar-
# produkt

# an

# ui ni Uhlerpakl

# Start converting file #9: 'section_000_009_t220.08.png' 
# ( la) re Penn
# u 474)

# Ve) =?) Vahkemat



if __name__ == "__main__":
    run_image_text_conversion()
    