"""MP4 из папок кадров с подписями (секвенсор Blender, H.264). blender --background --factory-startup
--python make_videos.py -- <папка labeled> <папка назначения> [имена через запятую]"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
src, dest = argv[0], argv[1]
only = argv[2].split(",") if len(argv) > 2 else None
os.makedirs(dest, exist_ok=True)
REPEAT = int(os.environ.get("VIDEO_REPEAT", "1"))  # сколько раз подряд показать ролик
SLOW = int(os.environ.get("VIDEO_SLOW", "1"))  # каждый кадр держится столько кадров (2 — вдвое медленнее)
SUFFIX = os.environ.get("VIDEO_SUFFIX", "")

for shot in sorted(os.listdir(src)):
    folder = os.path.join(src, shot)
    if not os.path.isdir(folder) or (only and shot not in only):
        continue
    files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
    if not files:
        continue
    files = [f for f in files for _ in range(SLOW)] * REPEAT
    scene = bpy.data.scenes.new("video_" + shot)
    bpy.context.window.scene = scene
    editor = scene.sequence_editor_create()
    strips = editor.strips if hasattr(editor, "strips") else editor.sequences
    strip = strips.new_image(shot, os.path.join(folder, files[0]), 1, 1)
    for f in files[1:]:
        strip.elements.append(f)
    image = bpy.data.images.load(os.path.join(folder, files[0]))
    scene.render.resolution_x, scene.render.resolution_y = image.size
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, len(files)
    scene.view_settings.view_transform = "Standard"
    scene.render.use_sequencer = True
    settings = scene.render.image_settings
    if "media_type" in settings.bl_rna.properties:
        settings.media_type = "VIDEO"
    settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.gopsize = 15
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.filepath = os.path.join(dest, shot + SUFFIX + ".mp4")
    scene.render.use_file_extension = False
    bpy.ops.render.render(animation=True, scene=scene.name)
    print("VIDEO_OK", shot, len(files), round(os.path.getsize(scene.render.filepath) / 1e6, 2), "МБ")
