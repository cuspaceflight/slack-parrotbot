import re, sys


class FrameBuffer:
    def __init__(self, width, height):
        self.reset_framebuffer(width, height)

    def reset_framebuffer(self, width, height):
        # why do I do this in such a weird way?
        # there's some weird mutability bug with Python here or something
        # so we have to create them as strings then convert to list apparently
        self.pixels = ['.' * width] * height
        self.pixels = [list(l) for l in self.pixels]

    def set_pixel(self, x, y, c):
        self.pixels[y][x] = c

    def __repr__(self):
        return '\n'.join([''.join(l) for l in self.pixels])


class TextBuffer(FrameBuffer):
    def __init__(self, fmap, width):
        c = fmap['A'].split('\n')
        self.char_width = len(c[0])
        self.char_height = len(c)
        self.fmap = fmap
        self.charmap = [""]
        self.width = (width-1) // self.char_width
        super().__init__(0, 0)

    def update_text(self, string):
        if not isinstance(string, str):
            raise TypeError("Argument must be string")

        if re.match(r'^[A-Za-z ]+$', string) is None:
            raise ValueError("String must be a-z (lower or upper) or spaces")

        screenwidth = min(len(string), self.width)

        cursor_x = 0
        charmap = [""]

        for word in string.upper().split(' '):
            if len(word) > screenwidth - cursor_x:
                if cursor_x > 0:
                    charmap[-1] += " " * (screenwidth - cursor_x)
                elif charmap[-1] == "":
                    charmap.pop()

                for i in range((len(word) // screenwidth) + 1):
                    charmap.append(word[i * screenwidth: (i+1) * screenwidth])
                cursor_x = len(word) % screenwidth
            else:
                charmap[-1] += word
                cursor_x += len(word)
    
            if cursor_x == screenwidth:
                cursor_x = 0
                charmap.append("")
            else:
                charmap[-1] += " "
                cursor_x += 1

        charmap[-1] += " " * (screenwidth - cursor_x)

        if charmap[-1] == " " * screenwidth:
            charmap.pop()

        self.charmap = charmap

        self.reset_framebuffer(
            width=(self.char_width * screenwidth + 1),
            height=(self.char_height * len(charmap) + 1)
        )

        for y, line in enumerate(charmap):
            for x, char in enumerate(line):
                charstring = self.fmap[char].split('\n')

                self.draw_char(
                        x * self.char_width + 1,
                        y * self.char_height + 1,
                        charstring
                )

    def draw_char(self, x, y, c):
        for i in range(self.char_width):
            for j in range(self.char_height):
                self.set_pixel(x+i, y+j, c[j][i])

