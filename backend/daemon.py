import subprocess
import time
import sys

def main():
    args = sys.argv[1:]
    scrap = True
    process = True
    update_known_stocks = True
    
    if "--scrap-only" in args or "-s" in args:
        process = False
    elif "--process-only" in args or "-p" in args:
        scrap = False

    while True:

        if scrap:
            print("-" * 40)
            print("STARTING SCRAPER")
            subprocess.run(["python", "scraper.py"])
            print("SCRAPER FINISHED")

        if process:
            print("-" * 40)
            print("STARTING PROCESSOR")
            subprocess.run(["python", "llm_processor.py"])
            print("PROCESSOR FINISHED")
            print("-" * 40)

        if update_known_stocks:
            print("-" * 40)
            print("STARTING STOCK NAME UPDATER")
            subprocess.run(["python", "update_known_stocks.py"])
            print("STOCK NAME UPDATER FINISHED")
            print("-" * 40)
            
        minutes = 10
        for i in range(0, minutes):
            print(f"Process will run again in {minutes-i} minutes")
            time.sleep(60)
            i += 1


if __name__ == "__main__":
    main()