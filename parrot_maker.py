from parrot_fontmap import *
import re
import sys

class ParrotMaker:
    def __init__(self, fmap=parrots_fontmap, max_width=40,
                 parrot_bg=":fireparrot:", parrot_fg = ":partyparrot:"):
        self.fmap = fmap
        self.parrot_fg = parrot_fg
        self.parrot_bg = parrot_bg

        if not isinstance(fmap, dict):
            raise TypeError("fmap must be a dict")
        if not all(chr(x) in fmap for x in range(ord("A"), ord("Z") + 1)):
            raise ValueError("fmap must contain A-Z")

        self.char_width = len(fmap["A"].split("\n")[0])
        if not all(len(fmap[chr(x)].split("\n")[0]) == self.char_width
                for x in range(ord("A"), ord("Z") + 1)):
            raise ValueError("Letters must be constant width")

        self.char_height = len(fmap["A"].split("\n"))
        if not all(len(fmap[chr(x)].split("\n")) == self.char_height
                for x in range(ord("A"), ord("Z") + 1)):
            raise ValueError("Letters must be constant height")

        # note that there is one char spacing and one char at each end
        self.width = (max_width - 1)//(self.char_width + 1)


    def to_parrots(self, string):
        if not isinstance(string, str):
            raise TypeError("1st argument must be string")
        if re.match(r'^[A-Za-z ]+$', string) is None:
            raise ValueError("String must be a-z (lower or upper) or spaces")

        # Split
        words = string.split(" ")
        lines = [""]
        for i in words:
            if len(lines[-1]) + 1 + len(i) <= self.width or lines[-1] == "":
                lines[-1] += ("" if lines[-1] == "" else " ") + i.upper()
            else:
                j = i
                while len(j) > 0:
                    lines.append(j[:self.width].upper())
                    j = j[self.width:]

        oldlines = [string.upper()[i:i+self.width]
                for i in range(0, len(string), self.width)]

        total_width = max(map(len, lines)) * (self.char_width + 1) + 1

        # Build lines
        out = ""
        for line in lines:
            out += "\n" + "".join((self.parrot_bg,) * total_width)
            for i in range(self.char_height):
                out += "\n" + self.parrot_bg
                counter = 1
                for j in line:
                    l = list(map(
                            lambda x:
                                self.parrot_bg if x == '.' else self.parrot_fg,
                            self.fmap[j].split("\n")[i]
                    ))
                    counter += len(l) + 1
                    out += "".join(l) + self.parrot_bg
                out += self.parrot_bg * (total_width - counter)

        out += "\n" + "".join((self.parrot_bg,) * total_width)
        return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Argument required")
        raise SystemExit

    pmaker = ParrotMaker()
    print(pmaker.to_parrots(" ".join(sys.argv[1:])))
