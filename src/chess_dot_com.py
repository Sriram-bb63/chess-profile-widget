import base64
from .cache import cache
from .constants_and_b64_assets import *
from .http_client import timed_get
from .utils import *


class ChessDotCom:

    def __init__(self):
        pass

    @staticmethod
    def validate_username(username):
        return bool(USERNAME_REGEX.fullmatch(username))

    @staticmethod
    @cache.memoize(timeout=CACHE_LONG_TTL)
    def get_profile_data(username):
        profile_url = f"{CHESS_DOT_COM_BASE_URL}/pub/player/{username}"
        profile_resp = timed_get(profile_url, headers=HEADERS)
        return profile_resp

    @staticmethod
    @cache.memoize(timeout=CACHE_SHORT_TTL)
    def get_player_stats(username):
        stats_url = f"{CHESS_DOT_COM_BASE_URL}/pub/player/{username}/stats"
        stats_resp = timed_get(stats_url, headers=HEADERS)
        return stats_resp

    @staticmethod
    def normalize_stats(stats):
        normalized_stats = copy.deepcopy(STATS_SCHEMA)
        if stats:
            if "last" in stats.keys() and "rating" in stats["last"].keys():
                normalized_stats["last"] = stats["last"]["rating"]
            if "best" in stats.keys() and "rating" in stats["best"].keys():
                normalized_stats["best"] = stats["best"]["rating"]
            if "record" in stats.keys() and "win" in stats["record"].keys():
                normalized_stats["wins"] = stats["record"]["win"]
            if "record" in stats.keys() and "draw" in stats["record"].keys():
                normalized_stats["draws"] = stats["record"]["draw"]
            if "record" in stats.keys() and "loss" in stats["record"].keys():
                normalized_stats["losses"] = stats["record"]["loss"]
        return normalized_stats

    @staticmethod
    @cache.memoize(timeout=CACHE_LONG_TTL)
    def generate_avatar_png_b64(avatar_url):
        avatar_resp = timed_get(avatar_url)
        return f"""data:image/png;base64,{base64.b64encode(avatar_resp.content).decode("utf-8")}"""

    @staticmethod
    def create_profile_summary(username):
        profile_summary = {}

        # Profile
        profile_resp = ChessDotCom.get_profile_data(username=username)
        if profile_resp.status_code != 200:
            return {"error": "Could not fetch profile data from chess.com"}
        profile_body = profile_resp.json()
        profile_summary["username"] = username
        profile_summary["avatar_url"] = profile_body.get("avatar")
        profile_summary["profile_url"] = profile_body["url"]
        profile_summary["title"] = profile_body.get("title")
        profile_summary["country_code"] = profile_body["country"].split("/")[-1]
        profile_summary["last_seen"] = format_last_online(
            timestamp=profile_body["last_online"]
        )
        profile_summary["joined"] = convert_epoch_to_month_year(
            timestamp=profile_body["joined"]
        )
        profile_summary["league"] = profile_body.get("league")

        # Stats
        stats_resp = ChessDotCom.get_player_stats(username=username)
        if stats_resp.status_code != 200:
            return {"error": "Could not fetch stats data from chess.com"}
        stats_body = stats_resp.json()
        profile_summary["stats"] = {}
        profile_summary["stats"]["rapid"] = ChessDotCom.normalize_stats(
            stats=stats_body.get("chess_rapid")
        )
        profile_summary["stats"]["blitz"] = ChessDotCom.normalize_stats(
            stats=stats_body.get("chess_blitz")
        )
        profile_summary["stats"]["bullet"] = ChessDotCom.normalize_stats(
            stats=stats_body.get("chess_bullet")
        )

        return profile_summary

    @staticmethod
    def generate_svg(
        player_data,
        theme,
        platform_logo,
    ):
        if theme not in THEMES.keys():
            theme = "default"
        colors = THEMES[theme]

        # Dynamic height based on footer presence
        svg_height = 300 if platform_logo else 265

        footer_section = (
            f"""<rect y="30" width="400" height="265" fill="{colors['fg']}" rx="12" ry="12"/>"""
            if platform_logo
            else ""
        )
        platform_logo = (
            f"""<image href="{CHESS_DOT_COM_LOGO}" height="20" x="11" y="269"/>"""
            if platform_logo
            else ""
        )
        background_svg = f"""<rect width="400" height="265" fill="{colors["bg"]}" rx="12" ry="12" />"""
        avatar_svg = f"""<a href="{player_data['profile_url']}" target="_blank"> <image href="{ChessDotCom.generate_avatar_png_b64(avatar_url=player_data['avatar_url']) if player_data['avatar_url'] else NO_AVATAR_PNG_B64}" x="11" y="15" width="75" height="75" clip-path="inset(0% round 5px)" /> </a>"""
        flag_svg = generate_flag_svg(country_code=player_data["country_code"])
        username_svg = f"""<a href="{player_data['profile_url']}" target="_blank"> <text x="100" y="35" fill="{colors["text-bright"]}" font-family="Arial" font-size="16" font-weight="bold">{fit_username(username=player_data['username'], font_size=16, max_width=180)}</text> </a>"""
        if player_data["league"]:
            league_svg = f"""<image href="{LEAGUES_SVG_B64[player_data['league'].lower()]}" x="100" y="50" width="30" /><text x="135" y="63" fill="{colors["text-mid"]}" font-family="Arial" font-size="11">{player_data['league']} league</text>"""
        else:
            league_svg = f"""<text x="100" y="63" fill="{colors["text-mid"]}" font-family="Arial" font-size="11">No league</text>"""
        if player_data["title"]:
            title_svg = f"""<image x="280" y="19" height="20" href="{TITLES_SVG_B64[player_data['title']]}"> </image>"""
            joined_svg_y = 55
            last_seen_svg_y = 70
        else:
            title_svg = ""
            joined_svg_y = 35
            last_seen_svg_y = 50
        joined_svg = f"""<text x="280" y="{joined_svg_y}" fill="{colors["text-light"]}" font-family="Arial" font-size="10">Joined: {player_data['joined']}</text>"""
        last_seen_svg = f"""<text x="280" y="{last_seen_svg_y}" fill="{colors["text-light"]}" font-family="Arial" font-size="10">Last seen: {player_data['last_seen']}</text>"""
        rapid_section = f"""<rect x="10" y="100" width="120" height="150" fill="{colors["fg"]}" rx="8" ry="8" /> <image href="{CHESS_DOT_COM_TIME_RAPID_SVG_B64}" x="30" y="112" width="25" /> <text x="80" y="130" fill="{colors["text-bright"]}" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle">Rapid</text> <text x="70" y="160" fill="{colors["text-bright"]}" font-family="Arial" font-size="22" font-weight="bold" text-anchor="middle">{player_data['stats']["rapid"]["last"]}</text> <text x="70" y="185" fill="{colors["text-mid"]}" font-family="Arial" font-size="12" text-anchor="middle">Highest</text> <text x="70" y="200" fill="{colors["text-mid"]}" font-family="Arial" font-size="14" text-anchor="middle">{player_data['stats']["rapid"]["best"]}</text> <text x="70" y="225" font-family="Arial" font-size="11" text-anchor="middle"> <tspan fill="{colors["win"]}">{player_data['stats']["rapid"]["wins"]}</tspan> <tspan fill="{colors["text-mid"]}">/</tspan> <tspan fill="{colors["draw"]}">{player_data['stats']["rapid"]["draws"]}</tspan> <tspan fill="{colors["text-mid"]}">/</tspan> <tspan fill="{colors["loss"]}">{player_data['stats']["rapid"]["losses"]}</tspan> </text>"""
        blitz_section = f"""<rect x="140" y="100" width="120" height="150" fill="{colors["fg"]}" rx="8" ry="8" /> <image href="{CHESS_DOT_COM_TIME_BLITZ_SVG_B64}" x="165" y="112" width="25" /> <text x="208" y="130" fill="{colors["text-bright"]}" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle">Blitz</text> <text x="200" y="160" fill="{colors["text-bright"]}" font-family="Arial" font-size="22" font-weight="bold" text-anchor="middle">{player_data['stats']["blitz"]["last"]}</text> <text x="200" y="185" fill="{colors["text-mid"]}" font-family="Arial" font-size="12" text-anchor="middle">Highest</text> <text x="200" y="200" fill="{colors["text-mid"]}" font-family="Arial" font-size="14" text-anchor="middle">{player_data['stats']["blitz"]["best"]}</text> <text x="200" y="225" font-family="Arial" font-size="11" text-anchor="middle"> <tspan fill="{colors["win"]}">{player_data['stats']["blitz"]["wins"]}</tspan> <tspan fill="{colors["text-mid"]}">/</tspan> <tspan fill="{colors["draw"]}">{player_data['stats']["blitz"]["draws"]}</tspan> <tspan fill="{colors["text-mid"]}">/</tspan> <tspan fill="{colors["loss"]}">{player_data['stats']["blitz"]["losses"]}</tspan> </text>"""
        bullet_section = f"""<rect x="270" y="100" width="120" height="150" fill="{colors["fg"]}" rx="8" ry="8" /> <image href="{CHESS_DOT_COM_TIME_BULLET_SVG_B64}" x="295" y="115" width="23" /> <text x="340" y="130" fill="{colors["text-bright"]}" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle">Bullet</text> <text x="330" y="160" fill="{colors["text-bright"]}" font-family="Arial" font-size="22" font-weight="bold" text-anchor="middle">{player_data['stats']["bullet"]["last"]}</text> <text x="330" y="185" fill="{colors["text-mid"]}" font-family="Arial" font-size="12" text-anchor="middle">Highest</text> <text x="330" y="200" fill="{colors["text-mid"]}" font-family="Arial" font-size="14" text-anchor="middle">{player_data['stats']["bullet"]["last"]}</text> <text x="330" y="225" font-family="Arial" font-size="11" text-anchor="middle"> <tspan fill="{colors["win"]}">{player_data['stats']["bullet"]["wins"]}</tspan> <tspan fill="{colors["text-mid"]}">/</tspan> <tspan fill="{colors["draw"]}">{player_data['stats']["bullet"]["draws"]}</tspan> <tspan fill="{colors["text-mid"]}">/</tspan> <tspan fill="{colors["loss"]}">{player_data['stats']["bullet"]["losses"]}</tspan> </text>"""
        svg = "".join(
            [
                f"""<svg width="400" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">""",
                footer_section,
                platform_logo,
                background_svg,
                avatar_svg,
                flag_svg,
                username_svg,
                league_svg,
                title_svg,
                joined_svg,
                last_seen_svg,
                rapid_section,
                blitz_section,
                bullet_section,
                """</svg>""",
            ]
        )
        return svg
