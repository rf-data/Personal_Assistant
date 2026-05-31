## streamlit_helper.py
# imports
from pathlib import Path
import os
import streamlit as st
import time
from datetime import datetime
import subprocess

from src.utils.general_helper import load_env_vars



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