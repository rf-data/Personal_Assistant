## streamlit_helper.py
# imports
from pathlib import Path
import os
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import time
from datetime import datetime
import subprocess

from src.utils.html_helper import read_html_file
from src.utils.general_helper import load_env_vars
from src.utils.text_file_helper import read_docx_text, read_text_file 


def st_file_preview(f_path: str|Path):

    match Path(f_path).suffix:
        case ".pdf":
            with open(f_path, "rb") as f:
                pdf_bytes = f.read()

            pdf_viewer(
                    input=pdf_bytes, 
                    # width=300
                    )
            
        case ".html":
            html_str = read_html_file(f_path)
            with st.expander(f"**File: '{Path(f_path).stem}'**"):
                st.html(html_str[:500])

        case ".json": 
            st.warning("not yet implemented")
        
        case ".docx": 
            # with open("temp.docx", "wb") as f:
            #     f.write(f_path.getbuffer())

            text = read_docx_text(f_path)
            st.markdown(text)
                    
            # st.warning("not yet implemented")

        case ".md" | ".txt": 
            txt_content = read_text_file(f_path)
            st.markdown(txt_content)

            # st.warning("not yet implemented")
            
    return 


def live_command_demo(cmd):
    # , log_name, mode="a"):
    placeholder = st.empty()
    start_time = datetime.now()

    process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
            )

    start_txt = f"""
{"=" * 80}
[START] {start_time.isoformat()} | CMD: {' '.join(cmd)}
{"=" * 80}

"""
    output = []
    output.append(start_txt)

    while True:

        line = process.stdout.readline()
        exit_code = process.poll()

        if line:
            output.append(line)

            placeholder.code(
                    "".join(output),
                    language="text"
                    )


        elif exit_code is not None:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            end_txt = f"""
{"=" * 80}
[END] {end_time.isoformat()} | EXIT CODE: {exit_code} | DURATION: {duration:.1f}s
{"=" * 80}

"""     
            
            output.append(end_txt)
            placeholder.code(
                    "".join(output),
                    language="text"
                    )
            
            break

        time.sleep(0.1)
    
    return process.returncode



def show_tree(path: str|Path=None, 
              level = 0, 
              max_depth=2):

    if not path:
        st.write("Please, select a folder to browse.")

        load_env_vars()
        data = os.getenv("DATA_DIR")

        if data is None:
            st.write("No default folder ('DATA_DIR') in '.env'.")
            return None
        
        path = data

    
    indent = "    " * level

    for item in sorted(Path(path).iterdir()):

        if item.is_dir() and level <= max_depth:

            with st.expander(f"{indent}📁 {item.name}"):

                show_tree(item, level + 1)

        else:
            st.write(f"{indent}📄 {item.name}")


# root = Path("data")

# show_tree(root)