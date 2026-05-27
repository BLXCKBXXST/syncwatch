"""Design tokens for Sonar PISh presentation."""
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# slide geometry (16:9)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# palette
BG_BASE = RGBColor(0xFF, 0xFF, 0xFF)
BG_MUTED = RGBColor(0xFA, 0xFA, 0xFA)
BG_ELEVATED = RGBColor(0xF1, 0xF5, 0xF9)
ACCENT = RGBColor(0x1E, 0x3A, 0x8A)
ACCENT_HOVER = RGBColor(0x1E, 0x40, 0xAF)
ACCENT_SOFT = RGBColor(0xDB, 0xEA, 0xFE)
FG_PRIMARY = RGBColor(0x0F, 0x17, 0x2A)
FG_SECONDARY = RGBColor(0x33, 0x41, 0x55)
FG_MUTED = RGBColor(0x64, 0x74, 0x8B)
BORDER = RGBColor(0xE5, 0xE7, 0xEB)
BORDER_STRONG = RGBColor(0xCB, 0xD5, 0xE1)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# fonts
FONT_SANS = "Inter"
FONT_MONO = "JetBrains Mono"

# typography sizes (pt)
TITLE_HERO = Pt(40)     # тема на титульном слайде
TITLE_H1 = Pt(28)       # заголовок внутреннего слайда
BODY = Pt(18)
BODY_SMALL = Pt(15)
META = Pt(13)
HEADER_MONO = Pt(11)
CODE = Pt(14)

# layout
PAD_X = Inches(0.6)
HEADER_Y = Inches(0.22)
HEADER_LINE_Y = Inches(0.6)
TITLE_Y = Inches(0.85)
TITLE_H = Inches(0.7)
ACCENT_BAR_Y = Inches(1.55)
ACCENT_BAR_W = Inches(0.6)
ACCENT_BAR_H = Inches(0.05)
CONTENT_Y = Inches(1.85)
CONTENT_H = Inches(5.3)
CONTENT_W = Inches(12.133)  # SLIDE_W - 2 * PAD_X

# brand strip
BRAND_TEXT = "Sonar · веб-платформа потокового видео"
TOTAL_SLIDES = 17
