import subprocess
import time
import sys

def get_project_root():
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)

def main():
    args = sys.argv[1:]
    scrap = True
    process = True
    update_known_stocks = True
    
    if "--scrap-only" in args or "-s" in args:
        process = False
    elif "--process-only" in args or "-p" in args:
        scrap = False

    project_root_directory = get_project_root()
    scraper_path = os.path.join(project_root_directory, "scraper", "main.py")
    analyzer_path = os.path.join(project_root_directory, "analyzer", "main.py")

    while True:

        if scrap:
            print("-" * 40)
            print("STARTING SCRAPER")
            subprocess.run(["python", scraper_path])
            print("SCRAPER FINISHED")

        if process:
            print("-" * 40)
            print("STARTING PROCESSOR")
            subprocess.run(["python", analyzer_path])
            print("PROCESSOR FINISHED")
            print("-" * 40)
            
        minutes = 10
        for i in range(0, minutes):
            print(f"Process will run again in {minutes-i} minutes")
            time.sleep(60)
            i += 1


if __name__ == "__main__":
    main()