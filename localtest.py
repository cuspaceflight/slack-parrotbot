from fontmap import parrots_fontmap, font_henry
from display import TextBuffer
import re, sys


class ParrotMaker:
    def __init__(self, fmap, max_width=40,
                 parrot_bg=":fireparrot:", parrot_fg = ":partyparrot:"):
        self.parrot_fg = parrot_fg
        self.parrot_bg = parrot_bg

        if not isinstance(fmap, dict):
            raise TypeError("fmap must be a dict")
        if not all(chr(x) in fmap for x in range(ord("A"), ord("Z") + 1)):
            raise ValueError("fmap must contain A-Z")

        char_width = len(fmap["A"].split("\n")[0])
        if not all(len(fmap[chr(x)].split("\n")[0]) == char_width
                for x in range(ord("A"), ord("Z") + 1)):
            raise ValueError("Letters must be constant width")

        char_height = len(fmap["A"].split("\n"))
        if not all(len(fmap[chr(x)].split("\n")) == char_height
                for x in range(ord("A"), ord("Z") + 1)):
            raise ValueError("Letters must be constant height")

        self.tb = TextBuffer(fmap, max_width)


    def to_parrots(self, string):
        self.tb.update_text(string)

        return ('WARNING: PARROTS\n' + str(self.tb)
                .replace('x', self.parrot_fg)
                .replace('.', self.parrot_bg))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Argument required")
        raise SystemExit

    pmaker = ParrotMaker(fmap=font_henry, max_width=40,
                         parrot_bg=':black_large_square:',
                         parrot_fg=':large_blue_square:')
    print(pmaker.to_parrots(" ".join(sys.argv[1:])))

