# import schedule
# import time
# import subprocess

# def run_script():
#     subprocess.run(["python", "script.py"])

# # Schedule the script to run every day at 2:30 PM
# schedule.every().day.at("14:30").do(run_script)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
# the above is without the update file


import schedule
import time
import subprocess
import os

def run_script():
    subprocess.run(["python", "script.py"])

# Schedule the script to run initially
schedule.every().day.at("14:30").do(run_script)

# Monitoring file for updates
update_file = "update.txt"

while True:
    # Check if the update file exists
    if os.path.exists(update_file):
        with open(update_file, "r") as file:
            new_schedule_time = file.read().strip()
            # Cancel the existing schedule
            schedule.clear()
            # Set the new schedule based on the received data
            schedule.every().day.at(new_schedule_time).do(run_script)
        # Remove the update file
        os.remove(update_file)

    schedule.run_pending()
    time.sleep(1)
