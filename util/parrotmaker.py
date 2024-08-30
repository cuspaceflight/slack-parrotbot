from sys import argv

from util.fontmap import fonts
from util.display import TextBuffer


class ParrotMaker:
	def __init__(self, fmap=fonts[0], max_width=30,):
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

	def to_parrots(self, string, bg=":fireparrot:", fg=":partyparrot:"):
		self.tb.update_text(string)
		return str(self.tb).replace('x', fg).replace('.', bg)


if __name__ == "__main__":
	if len(argv) < 2:
		print("Argument required")
		raise SystemExit

	pmaker = ParrotMaker()
	print(pmaker.to_parrots(" ".join(argv[1:])))
