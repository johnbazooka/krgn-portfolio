"""
PDF builder using ReportLab canvas.
Two layouts: single-column and two-column with sidebar.
"""

from datetime import datetime
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from . import styles as S
from .loader import build_cv_data, OUTPUT_DIR


def register_fonts():
    """Register Segoe UI fonts. Silently skips if not available."""
    for name, path in S.FUENTES["paths"].items():
        try:
            pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            pass


def _get_palette(name: str) -> dict:
    return S.PALETA.get(name, S.PALETA["azul_acero"])


def _wrap_text(text, font, size, max_width):
    """Word-wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}" if current else word
        if pdfmetrics.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class CVBuilder:
    """Builds a CV PDF from merged data."""

    def __init__(self, data: dict, output_path: Path):
        self.data = data
        self.output_path = output_path
        self.palette = _get_palette(data.get("paleta", "azul_acero"))
        self.W = S.PAGINA["ancho_mm"] * mm
        self.H = S.PAGINA["alto_mm"] * mm
        self.M = S.PAGINA["margen_mm"] * mm
        self.c = canvas.Canvas(str(output_path), pagesize=(self.W, self.H))

    def _draw_footer(self):
        c = self.c
        y = self.M - 4
        c.setFont(S.FUENTES["regular"], 7)
        c.setFillColor(self.palette["texto_claro"])
        nombre = self.data.get("persona", {}).get("nombre_completo", "")
        months_es = {
            "January": "Enero", "February": "Febrero", "March": "Marzo",
            "April": "Abril", "May": "Mayo", "June": "Junio",
            "July": "Julio", "August": "Agosto", "September": "Septiembre",
            "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
        }
        now = datetime.now()
        mes = months_es.get(now.strftime("%B"), now.strftime("%B"))
        text = f"CV {nombre} · {mes} {now.strftime('%Y')}"
        tw = c.stringWidth(text, S.FUENTES["regular"], 7)
        c.drawString((self.W - tw) / 2, y, text)

    def build(self):
        layout = self.data.get("layout", "single_col")
        if layout == "two_col_sidebar":
            self._build_two_col()
        else:
            self._build_single_col()
        self._draw_footer()
        self.c.save()

    def _draw_header(self, y_start, center_start, center_end):
        persona = self.data["persona"]
        nombre = persona.get("nombre_completo", "")
        objetivo = self.data.get("objetivo_laboral", "")

        c = self.c
        center_x = (center_start + center_end) / 2

        c.setFont(S.FUENTES["bold"], S.TAMANOS["nombre"])
        c.setFillColor(self.palette["titulo"])
        nw = c.stringWidth(nombre, S.FUENTES["bold"], S.TAMANOS["nombre"])
        c.drawString(center_x - nw / 2, y_start, nombre)

        y = y_start - 22
        c.setFont(S.FUENTES["semibold"], S.TAMANOS["seccion"])
        c.setFillColor(self.palette["texto_claro"])
        ow = c.stringWidth(objetivo, S.FUENTES["semibold"], S.TAMANOS["seccion"])
        c.drawString(center_x - ow / 2, y, objetivo)

        y -= 20
        contacto = persona.get("contacto", {})
        parts = []
        if contacto.get("telefono"):
            parts.append(("telefono", contacto["telefono"]))
        if contacto.get("email"):
            parts.append(("email", contacto["email"]))
        if contacto.get("celular"):
            parts.append(("telefono", contacto["celular"]))

        self._draw_contact_line(c, y, parts, center_start, center_end)
        return y - 28

    def _draw_contact_line(self, c, y, parts, area_start, area_end):
        SEP_W = 20
        font = S.FUENTES["regular"]
        emoji_font = S.FUENTES.get("emoji", font)
        size = S.TAMANOS["cuerpo"]

        pairs = []
        total_w = 0
        for key, value in parts:
            icon = S.EMOJIS.get(key, "")
            if icon:
                c.setFont(emoji_font, size)
                ew = c.stringWidth(icon, emoji_font, size) + 3
            else:
                ew = 0
            c.setFont(font, size)
            tw = c.stringWidth(value, font, size)
            pair_w = ew + tw
            pairs.append((icon, value, ew, tw, pair_w))
            total_w += pair_w

        total_w += SEP_W * (len(pairs) - 1)
        area_w = area_end - area_start
        x = area_start + (area_w - total_w) / 2

        c.setFillColor(self.palette["texto"])
        for icon, value, ew, tw, pair_w in pairs:
            if icon:
                c.setFont(emoji_font, size)
                c.drawString(x, y, icon)
                x += ew
            c.setFont(font, size)
            c.drawString(x, y, value)
            x += tw + SEP_W

    def _draw_section_title(self, y, title, x_start, x_end):
        self.c.setFont(S.FUENTES["bold"], S.TAMANOS["seccion"])
        self.c.setFillColor(self.palette["titulo"])
        self.c.drawString(x_start, y, title.upper())
        y -= 4
        self.c.setStrokeColor(self.palette["titulo"])
        self.c.setLineWidth(1.5)
        self.c.line(x_start, y, x_end, y)
        return y - S.INTERLINEA["seccion"] + 2

    def _draw_wrapped(self, y, text, x_start, max_width,
                      font=None, size=None, color=None, bullet=False):
        font = font or S.FUENTES["regular"]
        size = size or S.TAMANOS["cuerpo"]
        color = color or self.palette["texto"]

        prefix = "- " if bullet else ""
        full_text = prefix + text

        lines = _wrap_text(full_text, font, size, max_width)
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        inter = S.INTERLINEA["cuerpo"] if size >= S.TAMANOS["cuerpo"] else S.INTERLINEA["small"]
        for line in lines:
            self.c.drawString(x_start, y, line)
            y -= inter
        return y

    def _draw_experience(self, y, exp, x_start, x_end):
        c = self.c
        cargo = exp.get("cargo", "")
        periodo = exp.get("duracion_texto", "")
        max_w = x_end - x_start

        c.setFont(S.FUENTES["bold"], S.TAMANOS["cuerpo"])
        c.setFillColor(self.palette["titulo"])
        cargo_w = c.stringWidth(cargo, S.FUENTES["bold"], S.TAMANOS["cuerpo"])
        period_w = c.stringWidth(periodo, S.FUENTES["regular"], S.TAMANOS["small"])

        if cargo_w + period_w + 20 > max_w:
            cargo_lines = _wrap_text(
                cargo, S.FUENTES["bold"], S.TAMANOS["cuerpo"], max_w - 10
            )
            for cl in cargo_lines:
                c.setFont(S.FUENTES["bold"], S.TAMANOS["cuerpo"])
                c.drawString(x_start, y, cl)
                y -= 13
            c.setFont(S.FUENTES["regular"], S.TAMANOS["small"])
            c.setFillColor(self.palette["texto_claro"])
            c.drawString(x_start, y, periodo)
        else:
            c.drawString(x_start, y, cargo)
            c.setFont(S.FUENTES["regular"], S.TAMANOS["small"])
            c.setFillColor(self.palette["texto_claro"])
            c.drawString(x_end - period_w, y, periodo)
        y -= 11

        ubic = exp.get("ubicacion", "")
        if ubic:
            y = self._draw_wrapped(
                y, ubic, x_start, max_w,
                font=S.FUENTES["regular"], size=S.TAMANOS["tiny"],
                color=self.palette["texto_claro"]
            )

        y -= 1
        body_max = max_w - 10
        for resp in exp.get("responsabilidades", []):
            y = self._draw_wrapped(
                y, resp, x_start + 6, body_max, bullet=True,
                size=S.TAMANOS["small"]
            )

        logros = exp.get("logros", [])
        if logros:
            y -= 2
            c.setFont(S.FUENTES["bold"], S.TAMANOS["small"])
            c.setFillColor(self.palette["verde"])
            c.drawString(x_start, y, "Logros:")
            y -= S.INTERLINEA["small"]
            for logro in logros:
                y = self._draw_wrapped(
                    y, logro, x_start + 6, body_max, bullet=True,
                    size=S.TAMANOS["tiny"]
                )

        return y - 5

    def _draw_skills(self, y, habilidades, x_start, x_end):
        c = self.c
        max_w = x_end - x_start
        for cat_key, cat_data in habilidades.items():
            nombre = cat_data.get("nombre", cat_key)
            items = cat_data.get("items", [])
            line = f"{nombre}: {', '.join(items)}"
            lines = _wrap_text(
                line, S.FUENTES["regular"], S.TAMANOS["small"], max_w
            )
            c.setFont(S.FUENTES["regular"], S.TAMANOS["small"])
            c.setFillColor(self.palette["texto"])
            for ln in lines:
                c.drawString(x_start, y, ln)
                y -= S.INTERLINEA["small"]
            y -= 3
        return y

    def _build_single_col(self):
        x_start = self.M + 8
        x_end = self.W - self.M - 8
        max_w = x_end - x_start

        y = self._draw_header(self.H - self.M - 20, x_start, x_end)

        perfil = self.data.get("perfil_profesional", "")
        if perfil:
            y = self._draw_section_title(y, "Perfil Profesional", x_start, x_end)
            y = self._draw_wrapped(y, perfil, x_start, max_w)
            y -= 8

        exps = self.data.get("experiencia", [])
        if exps:
            y = self._draw_section_title(y, "Experiencia", x_start, x_end)
            y -= 4
            for exp in exps:
                y = self._draw_experience(y, exp, x_start, x_end)

        educacion = self.data.get("educacion", [])
        if educacion:
            y -= 4
            y = self._draw_section_title(y, "Educación", x_start, x_end)
            for edu in educacion:
                titulo = f"{edu.get('titulo', '')} - {edu.get('institucion', '')} ({edu.get('periodo', '')})"
                y = self._draw_wrapped(
                    y, titulo, x_start, max_w,
                    font=S.FUENTES["bold"], size=S.TAMANOS["cuerpo"]
                )

        habilidades = self.data.get("habilidades", {})
        if habilidades:
            y -= 4
            y = self._draw_section_title(y, "Habilidades", x_start, x_end)
            y = self._draw_skills(y, habilidades, x_start, x_end)

        idiomas = self.data.get("idiomas", [])
        if idiomas:
            y -= 4
            y = self._draw_section_title(y, "Idiomas", x_start, x_end)
            for idi in idiomas:
                line = f"{idi['idioma']} - {idi['nivel']}"
                y = self._draw_wrapped(y, line, x_start, max_w)

    def _build_two_col(self):
        c = self.c
        SIDEBAR_W = self.W * 0.30
        content_x = SIDEBAR_W + 5 * mm
        content_end = self.W - self.M - 4
        sidebar_x = self.M + 6
        sidebar_end = SIDEBAR_W - 6
        sidebar_max = sidebar_end - sidebar_x

        y = self._draw_header(self.H - self.M - 20, self.M, self.W - self.M)

        header_bottom = y + 16
        c.setFillColor(self.palette["fondo"])
        c.rect(0, 0, self.W, header_bottom, fill=1, stroke=0)
        c.setFillColor(self.palette["sidebar_bg"])
        c.rect(0, 0, SIDEBAR_W, header_bottom, fill=1, stroke=0)

        sy = header_bottom - 20
        cy = header_bottom - 20

        perfil = self.data.get("perfil_profesional", "")
        if perfil:
            sy = self._draw_section_title(sy, "Perfil", sidebar_x, sidebar_end)
            sy = self._draw_wrapped(
                sy, perfil, sidebar_x, sidebar_max,
                size=S.TAMANOS["small"]
            )
            sy -= 6

        habilidades = self.data.get("habilidades", {})
        if habilidades:
            sy = self._draw_section_title(sy, "Habilidades", sidebar_x, sidebar_end)
            for cat_key, cat_data in habilidades.items():
                items = cat_data.get("items", [])
                for item in items:
                    line = f"- {item}"
                    lines = _wrap_text(
                        line, S.FUENTES["regular"],
                        S.TAMANOS["small"], sidebar_max
                    )
                    c.setFont(S.FUENTES["regular"], S.TAMANOS["small"])
                    c.setFillColor(self.palette["texto"])
                    for ln in lines:
                        c.drawString(sidebar_x, sy, ln)
                        sy -= S.INTERLINEA["small"]
                sy -= 2
            sy -= 4

        educacion = self.data.get("educacion", [])
        if educacion:
            sy = self._draw_section_title(sy, "Educación", sidebar_x, sidebar_end)
            for edu in educacion:
                titulo = edu.get("titulo", "")
                inst = edu.get("institucion", "")
                c.setFont(S.FUENTES["bold"], S.TAMANOS["small"])
                c.setFillColor(self.palette["titulo"])
                titulo_lines = _wrap_text(
                    titulo, S.FUENTES["bold"],
                    S.TAMANOS["small"], sidebar_max
                )
                for ln in titulo_lines:
                    c.drawString(sidebar_x, sy, ln)
                    sy -= 11
                c.setFont(S.FUENTES["regular"], S.TAMANOS["tiny"])
                c.setFillColor(self.palette["texto_claro"])
                detail = f"{inst} ({edu.get('periodo', '')})"
                detail_lines = _wrap_text(
                    detail, S.FUENTES["regular"],
                    S.TAMANOS["tiny"], sidebar_max
                )
                for ln in detail_lines:
                    c.drawString(sidebar_x, sy, ln)
                    sy -= 10
                sy -= 4

        idiomas = self.data.get("idiomas", [])
        if idiomas:
            sy -= 4
            sy = self._draw_section_title(sy, "Idiomas", sidebar_x, sidebar_end)
            for idi in idiomas:
                line = f"{idi['idioma']} - {idi['nivel']}"
                c.setFont(S.FUENTES["regular"], S.TAMANOS["small"])
                c.setFillColor(self.palette["texto"])
                c.drawString(sidebar_x, sy, line)
                sy -= S.INTERLINEA["small"]

        cy = self._draw_section_title(cy, "Experiencia", content_x, content_end)
        cy -= 4
        for exp in self.data.get("experiencia", []):
            cy = self._draw_experience(cy, exp, content_x, content_end)


def generate_pdf(persona_id: str, derivative_id: str) -> Path:
    """Generate a CV PDF from a profile + derivative config."""
    register_fonts()
    data = build_cv_data(persona_id, derivative_id)
    output_dir = OUTPUT_DIR / persona_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{derivative_id}.pdf"
    builder = CVBuilder(data, output_path)
    builder.build()
    return output_path
