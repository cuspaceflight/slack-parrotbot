from parrotmaker import ParrotMaker
from sys import argv

if __name__ == "__main__":
    if len(argv) < 2:
        print("Argument required")
        raise SystemExit

    pmaker = ParrotMaker()
    print(pmaker.to_parrots(" ".join(argv[1:])))

