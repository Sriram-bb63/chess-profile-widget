import logging
import time

from flask import Flask, Response, g, request

from .cache import cache
from .constants_and_b64_assets import *
from .http_client import *
from .utils import *
from .chess_dot_com import ChessDotCom
from .lichess import Lichess

app = Flask(__name__)
app.config["CACHE_TYPE"] = "SimpleCache"
cache.init_app(app)
app.logger.setLevel(logging.INFO)


@app.before_request
def _start():
    g.t0 = time.perf_counter()


@app.after_request
def _end(resp):
    dur = time.perf_counter() - g.t0
    app.logger.info(f"total_time_ms={dur*1000:.1f}")
    return resp


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/widget")
def get_widget():

    platform = request.args.get("platform", None)
    username = request.args.get("username", "")
    theme = request.args.get("theme", "")
    logo_bool = True if request.args.get("logo", False) == "true" else False

    if not platform or platform not in ["chess-dot-com", "lichess"]:
        return {"error": "Empty/invalid platform"}, 400

    if platform == "chess-dot-com":
        is_username_valid = ChessDotCom.validate_username(username=username)
        if not is_username_valid:
            return {"error": "Invalid username"}, 400
        player_data = ChessDotCom.create_profile_summary(username=username)
        if "error" in player_data.keys():
            return player_data
        svg = ChessDotCom.generate_svg(
            player_data=player_data, theme=theme, platform_logo=logo_bool
        )
    elif platform == "lichess":
        player_data = Lichess.create_profile_summary(username=username)
        if "error" in player_data.keys():
            return player_data
        svg = Lichess.generate_svg(
            player_data=player_data, theme=theme, platform_logo=logo_bool
        )

    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


if __name__ == "__main__":
    app.run(debug=True)
