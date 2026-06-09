"""
MD2Image - Markdown 自动转图片插件

功能：
1. 自动检测 AI 回复中的 Markdown 格式，使用 Playwright + Chromium
   渲染为手账风格的高清图片。
2. 四套主题随机切换（绿野/晴蓝/绯红/金典），背景与配色自动适配。
3. 支持 /md2img 命令手动转换。
"""

import re
import random
import asyncio

import markdown
from playwright.async_api import async_playwright

from astrbot.api.star import Star, Context
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Plain, Image
from astrbot.api import logger
from astrbot.core.utils.io import save_temp_img


# ── 四套主题 CSS ────────────────────────────────────────────

THEME_CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}

/* ═══════════════════ 默认变量（绿野） ═══════════════════ */
:root, body[data-theme="green"] {
    --bg:            linear-gradient(180deg, #f8faf5 0%, #eef5ec 100%);
    --accent:        #4A7C5F;
    --accent-light:  #8BC4A1;
    --accent-soft:   #D4EADD;
    --accent-bg:     #f0f8f3;
    --heading:       #3D6B4F;
    --heading-bg:    linear-gradient(135deg, rgba(74,124,95,.12) 0%, rgba(139,196,161,.08) 100%);
    --h1-border:     #4A7C5F;
    --h2-color:      #3D6B4F;
    --h2-line:       #B8D9C5;
    --strong:        #2D5A3F;
    --em:            #5A8A6A;
    --code-bg:       #e8f2ec;
    --code-text:     #3D6B4F;
    --code-border:   #c8dfd2;
    --pre-bg:        #1e2d23;
    --pre-text:      #c8d6cc;
    --pre-border:    #2d4032;
    --quote-bg:      linear-gradient(135deg, #f0f8f3 0%, #e6f2e8 100%);
    --quote-border:  #4A7C5F;
    --quote-color:   #3D5A46;
    --quote-mark:    #8BC4A1;
    --table-th-bg:   #e6f2e8;
    --table-th-color:#3D6B4F;
    --table-border:  #c4dfcc;
    --table-even:    #f7faf5;
    --link:          #4A7C5F;
    --hr-color:      #B8D9C5;
    --ul-marker:     #4A7C5F;
    --ol-marker:     #3D6B4F;
    --top-deco:      linear-gradient(90deg, #4A7C5F, #8BC4A1, #4A7C5F);
    --bind-line:     #8BC4A1;
    --corner-color:  #8BC4A1;
    --footer-dot1:   #4A7C5F;
    --footer-dot2:   #8BC4A1;
    --footer-dot3:   #4A7C5F;
    --footer-text:   #9ABBA5;
    --footer-line:   #c4dfcc;
    --h3-prefix:     "🌿 ";
}

/* ═══════════════════ 晴蓝 ═══════════════════ */
body[data-theme="blue"] {
    --bg:            linear-gradient(180deg, #f5f8fc 0%, #e9f0f8 100%);
    --accent:        #3B6FB6;
    --accent-light:  #7EB8E0;
    --accent-soft:   #CDE3F2;
    --accent-bg:     #eef5fb;
    --heading:       #2C5282;
    --heading-bg:    linear-gradient(135deg, rgba(59,111,182,.12) 0%, rgba(126,184,224,.08) 100%);
    --h1-border:     #3B6FB6;
    --h2-color:      #2C5282;
    --h2-line:       #B0D0E8;
    --strong:        #1E4A7A;
    --em:            #4A7AAA;
    --code-bg:       #e8f0f8;
    --code-text:     #2C5282;
    --code-border:   #c8d8ea;
    --pre-bg:        #1a2740;
    --pre-text:      #c8d6e8;
    --pre-border:    #2a3a55;
    --quote-bg:      linear-gradient(135deg, #eef5fb 0%, #e2eef6 100%);
    --quote-border:  #3B6FB6;
    --quote-color:   #3A5270;
    --quote-mark:    #7EB8E0;
    --table-th-bg:   #e2eef6;
    --table-th-color:#2C5282;
    --table-border:  #c0d4e8;
    --table-even:    #f5f9fc;
    --link:          #3B6FB6;
    --hr-color:      #B0D0E8;
    --ul-marker:     #3B6FB6;
    --ol-marker:     #2C5282;
    --top-deco:      linear-gradient(90deg, #3B6FB6, #7EB8E0, #3B6FB6);
    --bind-line:     #7EB8E0;
    --corner-color:  #7EB8E0;
    --footer-dot1:   #3B6FB6;
    --footer-dot2:   #7EB8E0;
    --footer-dot3:   #3B6FB6;
    --footer-text:   #95B8D0;
    --footer-line:   #c0d4e8;
    --h3-prefix:     "◈ ";
}

/* ═══════════════════ 绯红 ═══════════════════ */
body[data-theme="red"] {
    --bg:            linear-gradient(180deg, #fef9f9 0%, #fdf3f4 100%);
    --accent:        #D4687C;
    --accent-light:  #F0B4C0;
    --accent-soft:   #FADDE2;
    --accent-bg:     #fef4f5;
    --heading:       #B84C5E;
    --heading-bg:    linear-gradient(135deg, rgba(212,104,124,.12) 0%, rgba(240,180,192,.08) 100%);
    --h1-border:     #D4687C;
    --h2-color:      #B84C5E;
    --h2-line:       #F0B4C0;
    --strong:        #A04050;
    --em:            #C87080;
    --code-bg:       #fdf0f2;
    --code-text:     #B84C5E;
    --code-border:   #f5d0d6;
    --pre-bg:        #2d1a20;
    --pre-text:      #e8c8ce;
    --pre-border:    #402a30;
    --quote-bg:      linear-gradient(135deg, #fef4f5 0%, #fce8ea 100%);
    --quote-border:  #D4687C;
    --quote-color:   #6B3A44;
    --quote-mark:    #F0B4C0;
    --table-th-bg:   #fce8ea;
    --table-th-color:#B84C5E;
    --table-border:  #f0c8ce;
    --table-even:    #fef9fa;
    --link:          #D4687C;
    --hr-color:      #F0B4C0;
    --ul-marker:     #D4687C;
    --ol-marker:     #B84C5E;
    --top-deco:      linear-gradient(90deg, #D4687C, #F0B4C0, #D4687C);
    --bind-line:     #F0B4C0;
    --corner-color:  #F0B4C0;
    --footer-dot1:   #D4687C;
    --footer-dot2:   #F0B4C0;
    --footer-dot3:   #D4687C;
    --footer-text:   #D0A0A8;
    --footer-line:   #f0c8ce;
    --h3-prefix:     "♡ ";
}

/* ═══════════════════ 金典 ═══════════════════ */
body[data-theme="gold"] {
    --bg:            linear-gradient(180deg, #fdf9f0 0%, #f7f0e0 100%);
    --accent:        #9B7D3C;
    --accent-light:  #D4B872;
    --accent-soft:   #EDE0C5;
    --accent-bg:     #faf6ed;
    --heading:       #7A5F2E;
    --heading-bg:    linear-gradient(135deg, rgba(155,125,60,.12) 0%, rgba(212,184,114,.08) 100%);
    --h1-border:     #9B7D3C;
    --h2-color:      #7A5F2E;
    --h2-line:       #D4B872;
    --strong:        #6B4F20;
    --em:            #9B8D6C;
    --code-bg:       #f7f1e4;
    --code-text:     #7A5F2E;
    --code-border:   #e8dcc8;
    --pre-bg:        #2d2618;
    --pre-text:      #e8dfc8;
    --pre-border:    #403a28;
    --quote-bg:      linear-gradient(135deg, #faf6ed 0%, #f5edd8 100%);
    --quote-border:  #9B7D3C;
    --quote-color:   #5A4A30;
    --quote-mark:    #D4B872;
    --table-th-bg:   #f5edd8;
    --table-th-color:#7A5F2E;
    --table-border:  #e0d3b8;
    --table-even:    #fdfaf4;
    --link:          #9B7D3C;
    --hr-color:      #D4B872;
    --ul-marker:     #9B7D3C;
    --ol-marker:     #7A5F2E;
    --top-deco:      linear-gradient(90deg, #9B7D3C, #D4B872, #9B7D3C);
    --bind-line:     #D4B872;
    --corner-color:  #D4B872;
    --footer-dot1:   #9B7D3C;
    --footer-dot2:   #D4B872;
    --footer-dot3:   #9B7D3C;
    --footer-text:   #C0B090;
    --footer-line:   #e0d3b8;
    --h3-prefix:     "❖ ";
}

/* ═══════════════════ 通用样式 ═══════════════════ */

body{
    font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",
                -apple-system,BlinkMacSystemFont,sans-serif;
    font-size:15px;line-height:1.85;color:#3d3d3d;
    background: var(--bg);
    max-width:680px;
    padding:32px 36px 24px 44px;
    position:relative;
}

/* ── 左侧装订线 ── */
body::before{
    content:"";position:fixed;top:0;left:22px;bottom:0;width:2px;
    background: repeating-linear-gradient(
        to bottom,
        var(--bind-line) 0px, var(--bind-line) 8px,
        transparent 8px, transparent 16px
    );
    opacity:0.55;z-index:0;
}

/* ── 四角装饰 ── */
body::after{
    content:"";position:fixed;pointer-events:none;z-index:0;
    top:10px;left:10px;right:10px;bottom:10px;
    border:1.5px solid var(--corner-color);
    opacity:0.25;border-radius:4px;
}
.corner{position:fixed;z-index:0;pointer-events:none;opacity:.45}
.corner-tl{top:8px;left:8px;width:20px;height:20px;
    border-top:2.5px solid var(--corner-color);
    border-left:2.5px solid var(--corner-color);
    border-radius:3px 0 0 0;}
.corner-tr{top:8px;right:8px;width:20px;height:20px;
    border-top:2.5px solid var(--corner-color);
    border-right:2.5px solid var(--corner-color);
    border-radius:0 3px 0 0;}
.corner-bl{bottom:8px;left:8px;width:20px;height:20px;
    border-bottom:2.5px solid var(--corner-color);
    border-left:2.5px solid var(--corner-color);
    border-radius:0 0 0 3px;}
.corner-br{bottom:8px;right:8px;width:20px;height:20px;
    border-bottom:2.5px solid var(--corner-color);
    border-right:2.5px solid var(--corner-color);
    border-radius:0 0 3px 0;}

/* ── 顶部装饰线 ── */
.page-top-deco{
    width:100%;height:3px;
    background: var(--top-deco);
    border-radius:2px;margin-bottom:20px;opacity:.7;
}

/* ── 标题 ── */
h1,h2,h3,h4,h5,h6{color:var(--heading);font-weight:700;margin-top:1.5em;margin-bottom:.45em;position:relative}
h1{
    font-size:1.55em;padding:6px 14px;margin-left:-8px;
    background: var(--heading-bg);
    border-left:4px solid var(--h1-border);
    border-radius:0 6px 6px 0;
}
h2{font-size:1.28em;color:var(--h2-color);padding-bottom:4px;
   border-bottom:2px dashed var(--h2-line)}
h3{font-size:1.1em;color:var(--accent)}
h3::before{content:var(--h3-prefix);color:var(--accent-light);font-size:.75em;position:relative;top:-2px}
p{margin:.7em 0}

/* ── 文本样式 ── */
strong{color:var(--strong);font-weight:700}
em{color:var(--em);font-style:italic}
del{text-decoration:line-through;color:#b0b0b0}

/* ── 行内代码 ── */
code{
    background:var(--code-bg);color:var(--code-text);
    padding:2px 8px;border-radius:6px;font-size:.9em;
    font-family:"Cascadia Code","Fira Code","JetBrains Mono",Consolas,monospace;
    border:1px solid var(--code-border);
}

/* ── 代码块 ── */
pre{
    background:var(--pre-bg);color:var(--pre-text);
    padding:18px 22px;border-radius:10px;overflow-x:auto;
    margin:1em 0;line-height:1.65;
    border:2px solid var(--pre-border);
    box-shadow:0 2px 8px rgba(0,0,0,.08);
}
pre code{background:none;color:inherit;padding:0;font-size:.88em;border:none}

/* ── 引用 ── */
blockquote{
    border-left:4px solid var(--quote-border);
    background: var(--quote-bg);
    margin:1em 0;padding:14px 18px;color:var(--quote-color);
    border-radius:0 10px 10px 0;position:relative;
}
blockquote::before{
    content:"❝";font-size:2em;color:var(--quote-mark);
    position:absolute;top:-8px;left:6px;opacity:.6;
}

/* ── 表格 ── */
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.95em;
      border-radius:8px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.05)}
th,td{border:1px solid var(--table-border);padding:10px 16px;text-align:left}
th{background:var(--table-th-bg);font-weight:700;color:var(--table-th-color)}
tr:nth-child(even) td{background:var(--table-even)}

/* ── 列表 ── */
ul,ol{padding-left:1.5em;margin:.55em 0}
li{margin:.4em 0}
ul>li::marker{color:var(--ul-marker)}
ol>li::marker{color:var(--ol-marker);font-weight:600}
li p{display:inline}

/* ── 链接 & 分割线 ── */
a{color:var(--link);text-decoration:none;border-bottom:1px dashed var(--accent-light)}
hr{border:none;height:1px;background:linear-gradient(90deg,transparent,var(--hr-color),transparent);margin:1.4em 0}

/* ── 代码高亮 ── */
.codehilite{
    background:var(--pre-bg);border-radius:10px;overflow:hidden;
    border:2px solid var(--pre-border);box-shadow:0 2px 8px rgba(0,0,0,.08);
}
.codehilite pre{margin:0;border:none;box-shadow:none}

/* ── 图片 ── */
img{max-width:100%;border-radius:10px;margin:.7em 0;border:2px solid var(--accent-soft)}

/* ── 页脚 ── */
.page-footer{
    margin-top:24px;padding-top:16px;
    text-align:center;font-size:12px;color:var(--footer-text);
    border-top:1px dashed var(--footer-line);
    display:flex;align-items:center;justify-content:center;gap:8px
}
.page-footer .dot{width:6px;height:6px;border-radius:50%;display:inline-block}
.page-footer .dot:nth-child(1){background:var(--footer-dot1)}
.page-footer .dot:nth-child(2){background:var(--footer-dot2)}
.page-footer .dot:nth-child(3){background:var(--footer-dot3)}
"""

THEME_NAMES = ["green", "blue", "red", "gold"]


class Main(Star):
    """Markdown 自动转图片插件——四主题手账风格。"""

    def __init__(self, context: Context) -> None:
        super().__init__(context)
        self._pending: dict[str, str] = {}
        self._browser = None
        self._playwright = None
        self._browser_lock = asyncio.Lock()

        self.min_length: int = 60
        self.viewport_width: int = 720
        self.device_scale_factor: float = 2.0

        self.md_patterns: list[tuple[str, str]] = [
            (r"\*\*[^*]+\*\*", "加粗"),
            (r"__[^_]+__", "加粗"),
            (r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)", "斜体"),
            (r"^#{1,6}\s", "标题"),
            (r"```", "代码块"),
            (r"`[^`]+`", "行内代码"),
            (r"^\s*[-*+]\s", "无序列表"),
            (r"^\s*\d+\.\s", "有序列表"),
            (r"\|.*\|", "表格"),
            (r"^>\s", "引用"),
            (r"~~[^~]+~~", "删除线"),
        ]

    # ── 生命周期 ────────────────────────────────────────────

    async def initialize(self) -> None:
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            logger.info("[md2image] Chromium 浏览器已启动")
        except Exception as e:
            logger.warning(f"[md2image] 浏览器启动失败: {e}")

    async def terminate(self) -> None:
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("[md2image] Chromium 已关闭")
        except Exception as e:
            logger.warning(f"[md2image] 浏览器关闭异常: {e}")

    # ── 浏览器管理 ──────────────────────────────────────────

    async def _get_browser(self):
        if self._browser and self._browser.is_connected():
            return self._browser
        async with self._browser_lock:
            if self._browser and self._browser.is_connected():
                return self._browser
            if not self._playwright:
                self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            logger.info("[md2image] Chromium 已重新启动")
            return self._browser

    # ── Markdown 检测 ───────────────────────────────────────

    def _has_markdown(self, text: str) -> bool:
        if len(text) < self.min_length:
            return False
        match_count = 0
        for pattern, _ in self.md_patterns:
            if re.search(pattern, text, re.MULTILINE):
                match_count += 1
                if match_count >= 2:
                    return True
        return False

    # ── HTML 构建 ───────────────────────────────────────────

    def _build_html(self, md_text: str, theme: str) -> str:
        html_body = markdown.markdown(
            md_text,
            extensions=["extra", "codehilite", "tables", "fenced_code"],
        )
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>{THEME_CSS}</style></head>
<body data-theme="{theme}">
<div class="corner corner-tl"></div>
<div class="corner corner-tr"></div>
<div class="corner corner-bl"></div>
<div class="corner corner-br"></div>
<div class="page-top-deco"></div>
{html_body}
<div class="page-footer">
    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
</div>
</body></html>"""

    # ── 渲染引擎 ────────────────────────────────────────────

    async def render_md_to_image(self, md_text: str, theme: str | None = None) -> str:
        if theme is None:
            theme = random.choice(THEME_NAMES)
        html = self._build_html(md_text, theme)
        browser = await self._get_browser()

        page = await browser.new_page(
            viewport={"width": self.viewport_width, "height": 1200},
            device_scale_factor=self.device_scale_factor,
        )
        try:
            await page.set_content(html, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(400)

            # 精准裁剪到 body 实际高度
            dimensions = await page.evaluate("""() => {
                const r = document.body.getBoundingClientRect();
                return { width: r.width, height: r.height };
            }""")
            await page.set_viewport_size({
                "width": self.viewport_width,
                "height": int(dimensions["height"]),
            })
            screenshot_bytes = await page.screenshot(type="png")
        finally:
            await page.close()

        logger.info(f"[md2image] 渲染完成，主题: {theme}")
        return save_temp_img(screenshot_bytes)

    # ── 自动检测钩子 ────────────────────────────────────────

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent) -> None:
        result = event.get_result()
        if not result or not result.chain:
            return
        chain = result.chain
        texts: list[str] = []
        plain_indices: list[int] = []
        for i, comp in enumerate(chain):
            if isinstance(comp, Plain):
                texts.append(comp.text)
                plain_indices.append(i)
        if not texts:
            return
        combined = "".join(texts)
        if not self._has_markdown(combined):
            return
        logger.info(f"[md2image] 检测到 MD 格式 ({len(combined)} 字)")
        try:
            img_path = await self.render_md_to_image(combined)
            for idx in sorted(plain_indices, reverse=True):
                del chain[idx]
            chain.insert(0, Image.fromFileSystem(img_path))
        except Exception as e:
            logger.error(f"[md2image] 渲染失败，保留原文: {e}")

    # ── 手动命令 ────────────────────────────────────────────

    @filter.command("md2img")
    async def handle_md2img(self, event: AstrMessageEvent):
        raw_text = event.message_str.strip()
        cmd_match = re.match(r"/md2img\s*", raw_text)
        md_content = raw_text[cmd_match.end():].strip() if cmd_match else ""
        if not md_content:
            session_id = event.get_session_id()
            stored = self._pending.get(session_id, "")
            if stored:
                md_content = stored
                self._pending.pop(session_id, None)
            else:
                self._pending[session_id] = ""
                yield event.plain_result("请在 30 秒内发送要转为图片的 Markdown：")
                return
        yield event.plain_result("正在使用 Chromium 渲染...")
        try:
            img_path = await self.render_md_to_image(md_content)
            yield event.image_result(img_path)
        except Exception as e:
            yield event.plain_result(f"渲染失败：{e}")
