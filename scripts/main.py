import sys
from browser import run

def main():
    oneshot = "--oneshot" in sys.argv
    print("Starting LinkedIn Connect Manager..." + (" (oneshot)" if oneshot else ""))
    run(oneshot=oneshot)

if __name__ == "__main__":
    main()
