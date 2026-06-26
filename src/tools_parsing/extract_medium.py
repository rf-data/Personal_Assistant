## extract_medium.py
# imports
import re
import json
import json5
from pathlib import Path
# from playwright.sync_api import sync_playwright

# from src.tools.extract_html import extract_html_file
from src.model_tools_parsing.html_extractor import HTMLCleanExtractor

from src.core.memory import RunContext
from src.core.logger import create_logger
from src.core.config import GeneralSettings, RunSettings
from src.utils.general_helper import load_env_vars 
from src.utils.path_helper import ensure_dir
from src.utils.text_file_helper import read_html_file   # , save_text_file
from src.utils.dict_helper import save_dict, get_yaml_config


# TO-DO: s. unten
"""
Deshalb ist gerendertes HTML oft besser

Wenn du:

page.content()

via Playwright nutzt, bekommst du:

finalen DOM,
oft bereits aufgelöste Bilder,
nach JS-Ausführung.

Das ist viel robuster.


from bs4 import BeautifulSoup
import json
import re


soup = BeautifulSoup(html, "html.parser")

scripts = soup.find_all("script")

apollo_text = None

for script in scripts:

    text = script.string

    if not text:
        continue

    if "window.__APOLLO_STATE__" in text:

        apollo_text = text
        break


if not apollo_text:
    raise ValueError("No APOLLO_STATE found")


json_text = apollo_text.split(
    "window.__APOLLO_STATE__ = ",
    1
)[1]

json_text = json_text.strip()

if json_text.endswith(";"):
    json_text = json_text[:-1]


data = json.loads(json_text)

print(data.keys())
"""

def extract_from_medium(f_path: str, 
                        run_context: RunContext,
                        extractor: HTMLCleanExtractor):

    save_folder = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data"
    html = read_html_file(f_path)
    url_extract = extractor.extract_apollo_html(html)
    
    f_name = run_context.run_id

    save_dict(data=url_extract.model_dump(), 
              path=Path(f"{save_folder}/{f_name}"))
    # now = run_context.timestamp
    # run_config = run_context.run_settings

    # run_context.save_folder
    # req_session = requests.Session()

    # PROFILE = "/home/robfra/playwright-medium-profile"
    # cookie_path = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/configuration/medium_cookies.json"
    # with open(cookie_path, "r") as f:
    #     cookies = json.load(f)

    # playwright_cookies = []

    # for c in cookies:

    #     cookie = {
    #             "name": c["name"],
    #             "value": c["value"],
    #             "domain": c["domain"],
    #             "path": c.get("path",
    #                         "/"),
    #             "httpOnly": c.get("httpOnly", False),
    #             "secure": c.get("secure", True),
    #             "sameSite": "None"
    #         }
    #     if "expirationDate" in c:
    #         cookie["expires"] = c["expirationDate"]

    #     playwright_cookies.append(cookie)

    # with sync_playwright() as p:

    #     # page = context.new_page()

    #     # page.goto("https://medium.com/m/signin")

        # page.pause()

        # input("Nach Login ENTER drücken")

        # context.storage_state(path="medium_auth.json")

        # context.close()
        # browser = p.chromium.launch(
        #                     headless=False
        #                 )

        # context = browser.new_context()
        # context.add_cookies(playwright_cookies)

        # page = context.new_page()

        # page.goto("https://medium.com")
        # page.wait_for_function(
        #             "() => window.__APOLLO_STATE__ !== undefined"
        #         )
        # # .wait_for_timeout(5000)  # wait_for_load_state("networkidle")

        # print(page.title())

        # input("ENTER")

        # html = page.content()

        # print("isLockedPreviewOnly:\n", 
        #       "isLockedPreviewOnly" in html)
        # print("lockedSource:\n", "lockedSource" in html)
        
        # browser.close()

        # # print("Bitte manuell einloggen...")
        # # input("ENTER drücken wenn Login fertig")

        # # context.storage_state(path="medium_auth.json")

        # # browser.close()

        # # browser = p.chromium.launch(
        # #     headless=True
        # # )
        # # context = browser.new_context(
        #         storage_state="medium_auth.json"
        #     )
        # page = context.new_page(
        #                 viewport={
        #                     "width": 1400,
        #                     "height": 2000
        #                     },
        #                 user_agent=(
        #                     "Mozilla/5.0 "
        #                     "(X11; Linux x86_64) "
        #                     "AppleWebKit/537.36 "
        #                     "(KHTML, like Gecko) "
        #                     "Chrome/136.0.0.0 "
        #                     "Safari/537.36"
        #                     )
        #                 )

        # page.goto(
        #     url,
        #     wait_until="networkidle",
        #     timeout=60000
        # )

        # page.wait_for_timeout(3000)

        # # optional:
        # # page.mouse.wheel(0, 5000)

        # f_path = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/Medium.html"
        # html = read_html_file(f_path) # page.content()


        # url_extract = extractor.extract_medium_scrape(html)
        # # match = re.search(
        #         r"window\.__APOLLO_STATE__\s*=\s*({.*?})\s*</script>",
        #         html,
        #         re.DOTALL
        #     )

        # if not match:
        #     raise ValueError("No APOLLO_STATE found")


        # json_text = match.group(1)

        # print(json_text[:500])

        # data = json5.loads(json_text)
        # print("DATA_KEYS:\n", data.keys())

        # data = json.loads(match.group(1))

        # dcf388a108c6
        
        # title = "Medium"
        # (
        #     page.title()
        #     .replace(" ", "_")
        #     .replace("/", "_")
        #     )

        # print("CONTENT:\n", html[:5000])

        # images = page.locator("img").evaluate_all(
        #     """
        #     imgs => imgs.map(
        #         img => ({
        #             src: img.src,
        #             alt: img.alt
        #         })
        #     )
        #     """
        # )

        # print("IMAGES:\n", images)

        # save_path = (
        #     Path(save_folder) /
        #     f"{title}"              # .html
        # )

        # ensure_dir(save_path)

        # save_path.write_text(
        #     html,
        #     encoding="utf-8"
        # )
        # print(f"Saved HTML to:\n{save_path}")

        # save_dict(data=medium_dict, path=save_path)
        # browser.close()
    # headers = {
    #         "User-Agent": (
    #             "Mozilla/5.0 (X11; Linux x86_64) "
    #             "AppleWebKit/537.36 "
    #             "(KHTML, like Gecko) "
    #             "Chrome/136.0.0.0 Safari/537.36"
    #         )
    #     }
 
    return html # html
   

if __name__ == "__main__":
    # url = "https://medium.com/algomart/how-to-structure-python-projects-in-2026-without-regretting-it-later-dcf388a108c6"
    medium_file = "/home/robfra/0_Portfolio_Projekte/gmp_compliance/data/medium_cookies.html"
    load_env_vars()

    general_config = get_yaml_config("extract_text", 
                                    model=GeneralSettings)

    
    run_config = get_yaml_config("run_args", 
                                    model=RunSettings)
    
    log_name = run_config.name_log
    name_logfile = run_config.name_logfile


    run_context = RunContext(
                    general_settings=general_config,
                    run_settings=run_config
    )

    logger = create_logger(name=log_name, file_name=f"{name_logfile}_1")
    run_context.logger = logger
    run_context.run_id = "MEDIUM_Python_cleaning_libraries"

    html_extractor = HTMLCleanExtractor(run_context) 
    extract_from_medium(f_path=medium_file,
                        run_context=run_context, 
                        extractor=html_extractor)