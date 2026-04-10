#!/usr/bin/env python3
"""Patch a generated Reveal.js export to play Teto_P1 on the first Time Out slide."""

from __future__ import annotations

import argparse
from pathlib import Path


START_MARKER = "<!-- Teto audio hook: start -->"
END_MARKER = "<!-- Teto audio hook: end -->"

AUDIO_HOOK = f"""{START_MARKER}
<script>
(function () {{
  "use strict";

  var TetoSlideAudio = {{
    targetHeading: "Time Out",
    audioPath: "audio/Teto_P1.wav",
    targetSlide: null,
    player: null,
    hasPlayed: false,
    isLocked: false,

    init: function () {{
      this.targetSlide = this.findFirstHeadingSlide(this.targetHeading);
      if (!this.targetSlide) {{
        console.warn("Teto audio: no slide found for", this.targetHeading);
        return;
      }}

      this.player = new Audio(this.audioPath);
      this.player.preload = "auto";
      this.player.addEventListener("ended", this.unlock.bind(this));
      this.player.addEventListener("error", this.unlock.bind(this));

      this.checkCurrentSlide();
      Reveal.on("beforeslidechange", this.preventLeavingTargetSlide.bind(this));
      Reveal.on("slidechanged", this.checkCurrentSlide.bind(this));
    }},

    findFirstHeadingSlide: function (headingText) {{
      var headings = document.querySelectorAll(".reveal .slides section h1, .reveal .slides section h2, .reveal .slides section h3");
      for (var i = 0; i < headings.length; i += 1) {{
        if (this.normalizeHeading(headings[i].textContent) === this.normalizeHeading(headingText)) {{
          return headings[i].closest("section");
        }}
      }}
      return null;
    }},

    normalizeHeading: function (text) {{
      return text.trim().replace(/[!?.]+$/, "").toLowerCase();
    }},

    checkCurrentSlide: function () {{
      if (!this.player || !this.targetSlide || this.hasPlayed) {{
        return;
      }}

      if (Reveal.getCurrentSlide() === this.targetSlide) {{
        this.play();
      }}
    }},

    play: function () {{
      var audio = this.player;
      audio.currentTime = 0;
      this.lock();

      var playPromise = audio.play();
      this.hasPlayed = true;

      if (playPromise && typeof playPromise.catch === "function") {{
        playPromise.catch(function () {{
          TetoSlideAudio.hasPlayed = false;
          TetoSlideAudio.retryAfterUserGesture();
        }});
      }}
    }},

    preventLeavingTargetSlide: function (event) {{
      if (!this.isLocked || Reveal.getCurrentSlide() !== this.targetSlide) {{
        return;
      }}

      event.preventDefault();
    }},

    lock: function () {{
      this.isLocked = true;
    }},

    unlock: function () {{
      this.isLocked = false;
    }},

    retryAfterUserGesture: function () {{
      var retry = function () {{
        document.removeEventListener("click", retry);
        document.removeEventListener("keydown", retry);
        document.removeEventListener("touchstart", retry);
        TetoSlideAudio.checkCurrentSlide();
      }};

      document.addEventListener("click", retry, {{ once: true }});
      document.addEventListener("keydown", retry, {{ once: true }});
      document.addEventListener("touchstart", retry, {{ once: true }});
    }}
  }};

  if (window.Reveal && Reveal.isReady && Reveal.isReady()) {{
    TetoSlideAudio.init();
  }} else if (window.Reveal) {{
    Reveal.on("ready", TetoSlideAudio.init.bind(TetoSlideAudio));
  }} else {{
    console.warn("Teto audio: Reveal.js was not available.");
  }}
}}());
</script>
{END_MARKER}"""


def remove_existing_hook(html: str) -> str:
    start = html.find(START_MARKER)
    if start == -1:
        return html

    end = html.find(END_MARKER, start)
    if end == -1:
      raise ValueError("Found the Teto audio start marker, but not the end marker.")

    return html[:start].rstrip() + "\n\n" + html[end + len(END_MARKER):].lstrip()


def patch_html(html: str) -> str:
    html = remove_existing_hook(html)
    body_close = html.rfind("</body>")
    if body_close == -1:
        raise ValueError("Could not find </body> in the HTML export.")

    return html[:body_close].rstrip() + "\n\n\t\t" + AUDIO_HOOK.replace("\n", "\n\t\t") + "\n\n" + html[body_close:]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject Teto_P1.wav playback into the first Reveal.js Time Out slide."
    )
    parser.add_argument(
        "html",
        nargs="?",
        default="index.html",
        help="Path to the generated Reveal.js HTML export. Defaults to index.html.",
    )
    args = parser.parse_args()

    html_path = Path(args.html)
    html = html_path.read_text(encoding="utf-8")
    patched_html = patch_html(html)
    html_path.write_text(patched_html, encoding="utf-8")
    print(f"Patched {html_path} to play audio/Teto_P1.wav on the first Time Out! slide.")


if __name__ == "__main__":
    main()
