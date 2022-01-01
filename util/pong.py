from util.display import FrameBuffer

class Pong:
	def __init__(self):
		self.fg = ':white_square:'
		self.bg = ':black_square:'

		self.w = 15
		self.h = 15
		self.paddlesize = 3

		self.fb = FrameBuffer(self.w, self.h)

		self.players = []

		self.p1 = self.h // 2 - self.paddlesize // 2
		self.p2 = self.p1

		self.vel = [0, 0]
		self.reset_ball_pos()

		self.start = False

	def reset_ball_pos(self):
		self.ball = [self.w // 2, self.h // 2]

	def update_screen(self):
		self.fb.reset_framebuffer(self.w, self.h)
		for i in range(self.paddlesize):
			self.fb.set_pixel(1, self.p1 + i, 'x')
			self.fb.set_pixel(self.w - 2, self.p2 + i, 'x')

		self.fb.set_pixel(self.ball[0], self.ball[1], 'x')

	def collision_handler(self, px, py):
		tmp_y = self.ball[1] + self.vel[1]

		if self.ball[0] == px and py <= tmp_y < py + self.paddlesize:
			if tmp_y - py < self.paddlesize // 2:
				self.vel[1] = -1
			else:
				self.vel[1] = 1
			self.vel[0] *= -1

	def tick(self):
		if not self.start:
			return

		self.ball[0] += self.vel[0]
		self.ball[1] += self.vel[1]

		# paddle 1 collision
		self.collision_handler(2, self.p1)
		self.collision_handler(self.w - 3, self.p2)

		if self.ball[0] == 0:
			self.start = False
			self.callback(f"<@{self.players[1]}> wins!")

		if self.ball[0] == self.w - 1:
			self.start = False
			self.callback(f"<@{self.players[0]}> wins!")

		if self.ball[1] in [0, self.h - 1]:
			self.vel[1] *= -1

	@property
	def screen(self):
		self.update_screen()
		return str(self.fb).replace('x', self.fg).replace('.', self.bg)
