#!/usr/bin/env python3
"""Patch a generated Reveal.js export to run the Teto audio sequence."""

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
    audioPaths: [
      "audio/Teto_P1.wav",
      "audio/Teto_P2.wav",
      "audio/Teto_P3.wav",
      "audio/Teto_P4.wav",
      "audio/Teto_P5.wav",
      "audio/Teto_P6.wav"
    ],
    targetSlide: null,
    players: [],
    activeIndex: -1,
    hasStarted: false,
    isAdvancing: false,
    isLocked: false,

    init: function () {{
      this.targetSlide = this.findFirstHeadingSlide(this.targetHeading);
      if (!this.targetSlide) {{
        console.warn("Teto audio: no slide found for", this.targetHeading);
        return;
      }}

      this.players = this.audioPaths.map(function (audioPath) {{
        var player = new Audio(audioPath);
        player.preload = "auto";
        player.addEventListener("ended", TetoSlideAudio.playNextStep.bind(TetoSlideAudio));
        player.addEventListener("error", TetoSlideAudio.abortSequence.bind(TetoSlideAudio));
        return player;
      }});

      this.checkCurrentSlide();
      Reveal.on("beforeslidechange", this.preventLeavingTargetSlide.bind(this));
      Reveal.on("slidechanged", this.checkCurrentSlide.bind(this));
      Reveal.on("fragmentshown", this.checkCurrentSlide.bind(this));
      Reveal.on("fragmenthidden", this.checkCurrentSlide.bind(this));
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
      if (!this.players.length || !this.targetSlide || this.hasStarted) {{
        return;
      }}

      if (Reveal.getCurrentSlide() === this.targetSlide) {{
        this.startSequence();
      }}
    }},

    startSequence: function () {{
      this.hasStarted = true;
      this.activeIndex = 0;
      this.lock();
      this.playCurrentLine();
    }},

    playCurrentLine: function () {{
      var audio = this.players[this.activeIndex];
      if (!audio) {{
        this.unlock();
        return;
      }}

      audio.currentTime = 0;
      this.lock();

      var playPromise = audio.play();

      if (playPromise && typeof playPromise.catch === "function") {{
        playPromise.catch(function () {{
          TetoSlideAudio.retryAfterUserGesture();
        }});
      }}
    }},

    playNextStep: function () {{
      if (this.activeIndex >= this.players.length - 1) {{
        this.unlock();
        return;
      }}

      this.activeIndex += 1;
      this.advanceDeck();
    }},

    advanceDeck: function () {{
      this.isAdvancing = true;
      Reveal.next();
      window.setTimeout(function () {{
        TetoSlideAudio.isAdvancing = false;
        TetoSlideAudio.playCurrentLine();
      }}, 350);
    }},

    preventLeavingTargetSlide: function (event) {{
      if (!this.isLocked || this.isAdvancing) {{
        return;
      }}

      event.preventDefault();
    }},

    lock: function () {{
      this.isLocked = true;
    }},

    unlock: function () {{
      this.isLocked = false;
      this.isAdvancing = false;
    }},

    abortSequence: function () {{
      console.warn("Teto audio: stopping the autoplay sequence after an audio error.");
      this.unlock();
    }},

    retryAfterUserGesture: function () {{
      var retry = function () {{
        document.removeEventListener("click", retry);
        document.removeEventListener("keydown", retry);
        document.removeEventListener("touchstart", retry);
        if (TetoSlideAudio.isLocked) {{
          TetoSlideAudio.playCurrentLine();
        }} else {{
          TetoSlideAudio.checkCurrentSlide();
        }}
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
        description="Inject the finite Teto audio autoplay sequence into the Reveal.js export."
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
    print(f"Patched {html_path} to run the Teto audio autoplay sequence.")


if __name__ == "__main__":
    main()
