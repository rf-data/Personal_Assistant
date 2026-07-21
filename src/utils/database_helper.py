import datetime
import shutil

timestamp = datetime.datetime.now().strftime("%Y%m%d")
shutil.copy("database.db", f"backup_{timestamp}.db")
