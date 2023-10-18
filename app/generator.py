from argparse import ArgumentParser
from decimal import Decimal
from random import seed

from app.main import generate_erlang

k = 3
a = Decimal("0.01455866498983198572668484397")

parser = ArgumentParser()
parser.add_argument("--batch", dest="batch", type=int, default=1)
parser.add_argument(
    "--infinite",
    dest="once",
    action="store_false",
)

if __name__ == "__main__":
    args = parser.parse_args()
    seed(53)
    while True:
        for _ in range(args.batch - 1):
            print(generate_erlang(a, k))
        print(generate_erlang(a, k), end="")
        if args.once:
            break
        try:
            input()
        except EOFError:
            break
    print()
