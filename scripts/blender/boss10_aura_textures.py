# Текстуры энергетической ауры Короля-дракона, этап C.2 (замечания владельца 2026-11-16: «не огонь, а магическое
# энергетическое поле»). Свои: процедурные шейдеры Blender (шум, полярные спирали, хребтовый шум), рендер Cycles с
# прозрачным фоном, цвета — глубокий фиолетовый, пурпур, маджента, светлые акценты. Кадры флипбуков собираются в
# сетку (Pillow не нужен: сетку собирает сам Blender через пиксели изображений).
# Запуск (без интерфейса):
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup \
#       -P scripts/blender/boss10_aura_textures.py -- assets/textures/vfx/boss10_aura_v2
# Файлы: flow_strip (лента потока, бесшовная по длине), bolt_strip (разряд, бесшовный), swirl_4x4 (вихрь, 16 кадров),
# veil_2x2 (полупрозрачная пелена, 4 вида), crackle_4x4 (треск разрядов, 16 кадров), orb_glow (мягкое свечение).

import math
import os
import sys
import tempfile

import bpy

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "aura_v2"
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)
FRAMES = tempfile.mkdtemp(prefix="aura_frames_")  # отдельные кадры флипбуков — во временной папке

# ── сцена: ортокамера на плоскость, только излучение ─────────────────────────────────────────────────────────────
scene = bpy.context.scene
for obj in list(bpy.data.objects):
	bpy.data.objects.remove(obj, do_unlink=True)
try:
	scene.render.engine = "CYCLES"
except TypeError as err:
	print("движок:", err)
scene.cycles.samples = 24
scene.cycles.device = "CPU"
scene.cycles.use_denoising = False
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.filter_size = 1.0

bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
plane = bpy.context.active_object
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, 0, 5)
scene.camera = cam

mat = bpy.data.materials.new("Aura")
plane.data.materials.append(mat)
nt = mat.node_tree


# ── маленький построитель выражений из нод ──────────────────────────────────────────────────────────────────────
class G:
	def __init__(self):
		nt.nodes.clear()
		self.uv = None

	def node(self, kind, **props):
		n = nt.nodes.new(kind)
		for k, v in props.items():
			setattr(n, k, v)
		return n

	def val(self, x):
		if isinstance(x, (int, float)):
			n = self.node("ShaderNodeValue")
			n.outputs[0].default_value = float(x)
			return n.outputs[0]
		return x

	def m(self, op, a, b=0.0, clamp=False):
		n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
		nt.links.new(self.val(a), n.inputs[0])
		if op not in ("ABSOLUTE", "SQRT", "COSINE", "SINE", "EXPONENT"):
			nt.links.new(self.val(b), n.inputs[1])
		return n.outputs[0]

	def add(self, a, b):
		return self.m("ADD", a, b)

	def sub(self, a, b):
		return self.m("SUBTRACT", a, b)

	def mul(self, a, b):
		return self.m("MULTIPLY", a, b)

	def smooth(self, x, lo, hi, to_lo=0.0, to_hi=1.0):
		n = self.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
		nt.links.new(self.val(x), n.inputs["Value"])
		n.inputs["From Min"].default_value = lo
		n.inputs["From Max"].default_value = hi
		n.inputs["To Min"].default_value = to_lo
		n.inputs["To Max"].default_value = to_hi
		return n.outputs[0]

	def coords(self):
		tc = self.node("ShaderNodeTexCoord")
		sep = self.node("ShaderNodeSeparateXYZ")
		nt.links.new(tc.outputs["UV"], sep.inputs[0])
		return sep.outputs[0], sep.outputs[1]

	def vec(self, x, y, z):
		n = self.node("ShaderNodeCombineXYZ")
		nt.links.new(self.val(x), n.inputs[0])
		nt.links.new(self.val(y), n.inputs[1])
		nt.links.new(self.val(z), n.inputs[2])
		return n.outputs[0]

	def noise(self, vector, w=0.0, scale=1.0, detail=2.0, rough=0.5, kind="FBM", dims="4D"):
		n = self.node("ShaderNodeTexNoise")
		n.noise_dimensions = dims
		try:
			n.noise_type = kind
		except Exception:
			pass
		nt.links.new(vector, n.inputs["Vector"])
		if dims == "4D":
			nt.links.new(self.val(w), n.inputs["W"])
		n.inputs["Scale"].default_value = scale
		n.inputs["Detail"].default_value = detail
		n.inputs["Roughness"].default_value = rough
		return n.outputs["Fac"]

	# периодическая по u (0…1) точка для шума: (cos 2πu, sin 2πu)·r — лента без шва
	def ring(self, u, r, z):
		a = self.mul(u, 2 * math.pi)
		return self.vec(self.mul(self.m("COSINE", a), r), self.mul(self.m("SINE", a), r), z)

	def output(self, intensity, stops):
		# intensity 0…1 → цвет и альфа по stops [(pos, (r,g,b,a)), …]
		ramp = self.node("ShaderNodeValToRGB")
		els = ramp.color_ramp.elements
		while len(els) > 1:
			els.remove(els[-1])
		els[0].position = stops[0][0]
		els[0].color = stops[0][1]
		for pos, col in stops[1:]:
			e = els.new(pos)
			e.color = col
		nt.links.new(self.val(intensity), ramp.inputs[0])
		emit = self.node("ShaderNodeEmission")
		nt.links.new(ramp.outputs["Color"], emit.inputs["Color"])
		emit.inputs["Strength"].default_value = 1.0
		transp = self.node("ShaderNodeBsdfTransparent")
		mix = self.node("ShaderNodeMixShader")
		nt.links.new(ramp.outputs["Alpha"], mix.inputs[0])
		nt.links.new(transp.outputs[0], mix.inputs[1])
		nt.links.new(emit.outputs[0], mix.inputs[2])
		out = self.node("ShaderNodeOutputMaterial")
		nt.links.new(mix.outputs[0], out.inputs["Surface"])


def hexc(h, a=1.0):
	h = h.lstrip("#")
	srgb = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
	# цвет ноды — линейный; «Standard» вернёт sRGB как задано
	lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
	return (lin[0], lin[1], lin[2], a)


# Палитра: глубокий фиолетовый → пурпур → маджента → светлый акцент
ENERGY = [
	(0.0, hexc("2a0660", 0.0)),
	(0.18, hexc("4a0f9a", 0.35)),
	(0.42, hexc("8a1fd6", 0.7)),
	(0.68, hexc("e040ff", 0.92)),
	(0.86, hexc("ff8af2", 1.0)),
	(1.0, hexc("fff0ff", 1.0)),
]
# пелена: облако — средний фиолет (читается и днём), прожилки — яркая маджента со светлыми кончиками
VEIL = [
	(0.0, hexc("3a0a7a", 0.0)),
	(0.22, hexc("5a1aa8", 0.42)),
	(0.5, hexc("a536ff", 0.72)),
	(0.78, hexc("ff6af0", 0.92)),
	(1.0, hexc("fff0ff", 1.0)),
]
SOFT = [
	(0.0, hexc("2a0660", 0.0)),
	(0.3, hexc("4a0f9a", 0.25)),
	(0.6, hexc("8a1fd6", 0.5)),
	(0.85, hexc("d24cff", 0.72)),
	(1.0, hexc("ffd6ff", 0.85)),
]


def frame_size(w, h):
	scene.render.resolution_x = w
	scene.render.resolution_y = h
	scene.render.resolution_percentage = 100
	aspect = h / w
	plane.scale = (1, aspect, 1)
	cam_data.ortho_scale = 2.0


def render(path):
	scene.render.filepath = path
	bpy.ops.render.render(write_still=True)


def grid(name, files, cols, rows, cell):
	# склеивает кадры (сверху слева, по строкам) в одну картинку — порядок флипбука Roblox
	W, H = cols * cell, rows * cell
	out = bpy.data.images.new(name, W, H, alpha=True)
	px = [0.0] * (W * H * 4)
	for i, f in enumerate(files):
		img = bpy.data.images.load(f)
		src = list(img.pixels)
		cx, cy = i % cols, i // cols
		oy = (rows - 1 - cy) * cell  # пиксели Blender — снизу вверх
		for y in range(cell):
			row = (oy + y) * W + cx * cell
			s = y * cell * 4
			px[row * 4 : (row + cell) * 4] = src[s : s + cell * 4]
		bpy.data.images.remove(img)
	out.pixels = px
	out.filepath_raw = os.path.join(OUT, name + ".png")
	out.file_format = "PNG"
	out.save()


# ── 1. Лента потока: три сплетённые нити с бусинами света, лёгкая дымка; бесшовна по длине ───────────────────────
def flow_strip():
	g = G()
	u, v = g.coords()
	total = g.val(0.0)
	# толстые нити (видно с 40–60 стадов): ядро ~6 % высоты ленты, ореол ~30 %, между нитями — плотная дымка
	for i, (r, amp, core, glow, beads) in enumerate(
		[(1.1, 0.3, 0.032, 0.15, 3), (1.6, 0.26, 0.026, 0.13, 5), (0.8, 0.34, 0.02, 0.11, 2)]
	):
		n = g.noise(g.ring(u, r, 3.7 * i + 1.3), scale=1.2, detail=2.0, dims="3D")
		off = g.mul(g.sub(n, 0.5), amp * 2)
		d = g.m("ABSOLUTE", g.sub(g.sub(v, 0.5), off))
		line = g.add(g.mul(g.smooth(d, core * 2, 0.0), 0.8), g.mul(g.smooth(d, glow, 0.0), 0.45))
		bead = g.m("POWER", g.add(g.mul(g.m("COSINE", g.mul(u, 2 * math.pi * beads)), 0.5), 0.5), 3.0)
		total = g.m("MAXIMUM", total, g.mul(line, g.add(0.6, g.mul(bead, 0.4))))
	haze = g.mul(g.noise(g.ring(u, 2.2, g.mul(v, 2.5)), scale=1.5, detail=4.0, dims="3D"), 0.5)
	edge = g.mul(g.smooth(v, 0.02, 0.22), g.smooth(v, 0.98, 0.78))
	total = g.mul(g.m("MAXIMUM", total, g.mul(haze, g.smooth(g.m("ABSOLUTE", g.sub(v, 0.5)), 0.46, 0.08))), edge)
	g.output(g.m("MINIMUM", total, 1.0), ENERGY)
	frame_size(512, 128)
	render(os.path.join(OUT, "flow_strip.png"))


# ── 2. Разряд: ломаная молния с ярким ядром и маджента-ореолом; бесшовна по длине ──────────────────────────────
def bolt_strip():
	g = G()
	u, v = g.coords()
	n1 = g.noise(g.ring(u, 2.0, 5.0), scale=1.4, detail=8.0, rough=0.72, dims="3D")
	n2 = g.noise(g.ring(u, 6.0, 9.0), scale=1.0, detail=4.0, rough=0.6, dims="3D")
	off = g.add(g.mul(g.sub(n1, 0.5), 0.9), g.mul(g.sub(n2, 0.5), 0.25))
	d = g.m("ABSOLUTE", g.sub(g.sub(v, 0.5), off))
	core = g.smooth(d, 0.022, 0.0)
	glow = g.mul(g.smooth(d, 0.16, 0.0), 0.5)
	flicker = g.add(0.7, g.mul(g.noise(g.ring(u, 3.0, 1.0), scale=2.0, detail=1.0, dims="3D"), 0.6))
	edge = g.mul(g.smooth(v, 0.0, 0.2), g.smooth(v, 1.0, 0.8))
	total = g.mul(g.mul(g.m("MAXIMUM", core, glow), flicker), edge)
	g.output(g.m("MINIMUM", total, 1.0), ENERGY)
	frame_size(512, 64)
	render(os.path.join(OUT, "bolt_strip.png"))


def polar(g):
	u, v = g.coords()
	x, y = g.sub(u, 0.5), g.sub(v, 0.5)
	r = g.m("SQRT", g.add(g.mul(x, x), g.mul(y, y)))
	a = g.m("ARCTAN2", y, x)
	return x, y, r, a


# ── 3. Вихрь: три спиральных рукава закручиваются и расходятся, 16 кадров (OneShot: появляется и тает) ─────────
def swirl(t, path):
	g = G()
	x, y, r, a = polar(g)
	grow = 0.75 + 0.35 * t
	rr = g.mul(r, 1 / grow)
	spin = 2 * math.pi * 0.9 * t
	# широкие рукава (3) и тонкие встречные нити (5) — вихрь «плетётся», а не крутится вертушкой
	phase = g.add(g.add(g.mul(a, 3.0), g.mul(rr, -16.0)), spin)
	arms = g.m("POWER", g.add(g.mul(g.m("COSINE", phase), 0.5), 0.5), 5.0)
	phase2 = g.add(g.add(g.mul(a, 5.0), g.mul(rr, 22.0)), -1.6 * spin)
	threads = g.m("POWER", g.add(g.mul(g.m("COSINE", phase2), 0.5), 0.5), 28.0)
	breakup = g.noise(g.vec(g.mul(x, 4), g.mul(y, 4), 0.0), w=t * 1.5, scale=2.0, detail=3.0)
	ridge = g.noise(g.vec(g.mul(x, 6), g.mul(y, 6), 0.0), w=t * 2.0 + 4.0, scale=2.5, detail=4.0)
	fil = g.m("POWER", g.sub(1.0, g.mul(g.m("ABSOLUTE", g.sub(ridge, 0.5)), 2.0)), 6.0)
	band = g.mul(g.smooth(rr, 0.04, 0.16), g.smooth(rr, 0.46, 0.28))
	env = math.sin(math.pi * (0.08 + 0.92 * t)) ** 0.6
	core = g.mul(g.smooth(rr, 0.12, 0.0), 0.3)
	body = g.mul(arms, g.add(0.35, g.mul(breakup, 0.55)))
	total = g.add(g.add(body, g.mul(threads, 0.55)), g.mul(fil, g.mul(arms, 0.6)))
	total = g.mul(g.add(total, core), g.mul(band, env))
	g.output(g.m("MINIMUM", total, 1.0), ENERGY)
	render(path)


# ── 4. Пелена: полупрозрачное облако энергии с прожилками, 4 разных вида (Random) ──────────────────────────────
def veil(seed, path):
	g = G()
	x, y, r, a = polar(g)
	p = g.vec(g.mul(x, 3.0), g.mul(y, 3.0), 0.0)
	cloud = g.noise(p, w=seed, scale=1.6, detail=6.0, rough=0.55)
	ridge = g.noise(p, w=seed + 7.0, scale=2.2, detail=5.0, rough=0.6)
	vein = g.m("POWER", g.sub(1.0, g.mul(g.m("ABSOLUTE", g.sub(ridge, 0.5)), 2.0)), 9.0)
	fall = g.smooth(r, 0.5, 0.12)
	total = g.mul(g.add(g.mul(g.smooth(cloud, 0.35, 0.8), 0.55), g.mul(vein, 0.6)), fall)
	g.output(g.m("MINIMUM", total, 1.0), VEIL)
	render(path)


# ── 5. Треск: тонкие ломаные дуги вспыхивают и гаснут, 16 кадров (OneShot) ─────────────────────────────────────
def crackle(t, path):
	g = G()
	x, y, r, a = polar(g)
	p = g.vec(g.mul(x, 2.6), g.mul(y, 2.6), 0.0)
	# изолиния шума (|n − 0.5| ≈ 0) — тонкая ломаная дуга; низкая шероховатость — меньше «клякс»
	n = g.noise(p, w=2.0 + t * 0.6, scale=1.6, detail=5.0, rough=0.5)
	d = g.m("ABSOLUTE", g.sub(n, 0.5))
	line = g.add(g.smooth(d, 0.016, 0.0), g.mul(g.smooth(d, 0.07, 0.0), 0.45))
	sparse = g.smooth(g.noise(p, w=11.0, scale=1.3, detail=1.0), 0.4, 0.56)
	fall = g.smooth(r, 0.48, 0.15)
	env = min(1.0, (t + 0.07) / 0.14) if t < 0.07 else max(0.0, 1.0 - (t - 0.07) / 0.93) ** 0.8
	total = g.mul(g.mul(g.mul(line, sparse), g.mul(fall, env)), 1.5)
	g.output(g.m("MINIMUM", total, 1.0), ENERGY)
	render(path)


# ── 6. Мягкое объёмное свечение с лёгкой неоднородностью ───────────────────────────────────────────────────────
def orb_glow():
	g = G()
	x, y, r, a = polar(g)
	n = g.noise(g.vec(g.mul(x, 3), g.mul(y, 3), 0.0), w=3.0, scale=1.5, detail=3.0)
	base = g.m("POWER", g.smooth(r, 0.5, 0.0), 2.2)
	total = g.mul(base, g.add(0.75, g.mul(n, 0.4)))
	g.output(g.m("MINIMUM", total, 1.0), SOFT)
	frame_size(256, 256)
	render(os.path.join(OUT, "orb_glow.png"))


def flipbook(name, fn, count, cols, cell, args):
	frame_size(cell, cell)
	files = []
	for i in range(count):
		f = os.path.join(FRAMES, f"{name}_{i:02d}.png")
		fn(args(i), f)
		files.append(f)
	grid(name, files, cols, count // cols, cell)


flow_strip()
bolt_strip()
orb_glow()
flipbook("swirl_4x4", swirl, 16, 4, 256, lambda i: i / 15)
flipbook("veil_2x2", veil, 4, 2, 512, lambda i: 3.1 * i + 0.7)
flipbook("crackle_4x4", crackle, 16, 4, 256, lambda i: i / 15)
print("ГОТОВО", OUT)
