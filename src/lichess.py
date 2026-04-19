import concurrent.futures
import copy

import requests

from .cache import cache
from .constants_and_b64_assets import *
from .utils import *


class Lichess:

    def __init__(self):
        pass

    @staticmethod
    @cache.memoize(timeout=CACHE_LONG_TTL)
    def get_profile_data(username):
        profile_url = f"{LICHESS_BASE_URL}/api/user/{username}"
        profile_resp = requests.get(profile_url, headers=HEADERS)
        return profile_resp

    @staticmethod
    @cache.memoize(timeout=CACHE_SHORT_TTL)
    def get_rapid_stats(username):
        rapid_url = f"{LICHESS_BASE_URL}/api/user/{username}/perf/rapid"
        rapid_resp = requests.get(rapid_url, headers=HEADERS)
        return rapid_resp

    @staticmethod
    @cache.memoize(timeout=CACHE_SHORT_TTL)
    def get_blitz_stats(username):
        blitz_url = f"{LICHESS_BASE_URL}/api/user/{username}/perf/blitz"
        blitz_resp = requests.get(blitz_url, headers=HEADERS)
        return blitz_resp

    @staticmethod
    @cache.memoize(timeout=CACHE_SHORT_TTL)
    def get_bullet_stats(username):
        bullet_url = f"{LICHESS_BASE_URL}/api/user/{username}/perf/bullet"
        bullet_resp = requests.get(bullet_url, headers=HEADERS)
        return bullet_resp

    @staticmethod
    def normalize_stats(rapid_stats, blitz_stats, bullet_stats):
        rapid_normalized_stats = copy.deepcopy(STATS_SCHEMA)
        rapid_normalized_stats["last"] = round(rapid_stats["perf"]["glicko"]["rating"])
        best_rapid = rapid_stats["stat"].get("highest", {}).get("int", "N/A")
        rapid_normalized_stats["best"] = (
            round(best_rapid) if best_rapid != "N/A" else "N/A"
        )
        rapid_normalized_stats["wins"] = rapid_stats["stat"]["count"]["win"]
        rapid_normalized_stats["draws"] = rapid_stats["stat"]["count"]["draw"]
        rapid_normalized_stats["losses"] = rapid_stats["stat"]["count"]["loss"]

        blitz_normalized_stats = copy.deepcopy(STATS_SCHEMA)
        blitz_normalized_stats["last"] = round(blitz_stats["perf"]["glicko"]["rating"])
        best_blitz = blitz_stats["stat"].get("highest", {}).get("int", "N/A")
        blitz_normalized_stats["best"] = (
            round(best_blitz) if best_blitz != "N/A" else "N/A"
        )
        blitz_normalized_stats["wins"] = blitz_stats["stat"]["count"]["win"]
        blitz_normalized_stats["draws"] = blitz_stats["stat"]["count"]["draw"]
        blitz_normalized_stats["losses"] = blitz_stats["stat"]["count"]["loss"]

        bullet_normalized_stats = copy.deepcopy(STATS_SCHEMA)
        bullet_normalized_stats["last"] = round(
            bullet_stats["perf"]["glicko"]["rating"]
        )
        best_bullet = bullet_stats["stat"].get("highest", {}).get("int", "N/A")
        bullet_normalized_stats["best"] = (
            round(best_bullet) if best_bullet != "N/A" else "N/A"
        )
        bullet_normalized_stats["wins"] = bullet_stats["stat"]["count"]["win"]
        bullet_normalized_stats["draws"] = bullet_stats["stat"]["count"]["draw"]
        bullet_normalized_stats["losses"] = bullet_stats["stat"]["count"]["loss"]

        return rapid_normalized_stats, blitz_normalized_stats, bullet_normalized_stats

    @staticmethod
    def create_profile_summary(username):
        profile_summary = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            profile_future = executor.submit(Lichess.get_profile_data, username)
            rapid_future = executor.submit(Lichess.get_rapid_stats, username)
            blitz_future = executor.submit(Lichess.get_blitz_stats, username)
            bullet_future = executor.submit(Lichess.get_bullet_stats, username)
            profile_resp = profile_future.result()
            rapid_resp = rapid_future.result()
            blitz_resp = blitz_future.result()
            bullet_resp = bullet_future.result()

        # Profile
        if profile_resp.status_code != 200:
            return {"error": "Could not fetch profile data from lichess.org"}
        profile_body = profile_resp.json()
        is_acc_disabled = profile_body.get("disabled")
        if is_acc_disabled:
            return {"error": "Lichess account is disabled"}
        profile_summary["username"] = username
        profile_summary["profile_url"] = profile_body.get("url")
        profile_summary["flair"] = profile_body.get("flair")
        profile_summary["bio"] = profile_body.get("profile", {}).get("bio")
        profile_summary["country_code"] = profile_body.get("profile", {}).get("flag")
        profile_summary["joined"] = convert_epoch_to_month_year(
            timestamp=profile_body.get("createdAt"), unit="ms"
        )
        profile_summary["last_seen"] = format_last_online(
            timestamp=profile_body.get("seenAt"), unit="ms"
        )
        profile_summary["play_time"] = convert_secs_to_hours_mins(
            secs=profile_body.get("playTime", {}).get("total", 0)
        )
        profile_summary["patron_wings_color"] = profile_body.get("patronColor")
        profile_summary["title"] = profile_body.get("title")

        # Stats
        if (
            rapid_resp.status_code != 200
            or blitz_resp.status_code != 200
            or bullet_resp.status_code != 200
        ):
            return {"error": "Could not fetch player stats from lichess.org"}
        rapid_body = rapid_resp.json()
        blitz_body = blitz_resp.json()
        bullet_body = bullet_resp.json()
        profile_summary["stats"] = {}
        (
            profile_summary["stats"]["rapid"],
            profile_summary["stats"]["blitz"],
            profile_summary["stats"]["bullet"],
        ) = Lichess.normalize_stats(
            rapid_stats=rapid_body, blitz_stats=blitz_body, bullet_stats=bullet_body
        )
        return profile_summary

    @staticmethod
    def generate_flag_svg(country_code, x_pos):
        if country_code not in FLAG_COORDINATES.keys():
            return ""
        return f"""<svg x="{x_pos}" y="18" width="25" height="25" viewBox="0 0 32 24" overflow="hidden"> <image href="{FLAGS_PNG_B64}" x="{FLAG_COORDINATES[country_code][0]}" y="{FLAG_COORDINATES[country_code][1]}"></image> </svg>"""

    @staticmethod
    def split_bio_text(bio, font_size, max_width):
        if get_string_width(bio, font_size) <= max_width:
            return [bio]

        words = bio.split()
        first_line = ""
        remaining_words = []
        for i, word in enumerate(words):
            test_line = first_line + (" " if first_line else "") + word
            if get_string_width(test_line, font_size) <= max_width:
                first_line = test_line
            else:
                remaining_words = words[i:]
                break

        if not remaining_words:
            return [first_line]

        second_line = " ".join(remaining_words)

        if get_string_width(second_line, font_size) > max_width:
            low, high = 0, len(second_line)
            best_fit = ""
            while low <= high:
                mid = (low + high) // 2
                candidate = second_line[:mid] + "..."
                if get_string_width(candidate, font_size) <= max_width:
                    best_fit = candidate
                    low = mid + 1
                else:
                    high = mid - 1
            second_line = best_fit if best_fit else "..."

        return [first_line, second_line]

    @staticmethod
    def normalize_time_spent(time_spent):
        h = time_spent[0]
        m = time_spent[1]
        if h > 999:
            return "999+ hours"
        if m < 30:
            return f"~{h} hours"
        else:
            return f"~{h+1} hours"

    @staticmethod
    def generate_svg(player_data, theme, platform_logo):
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
            f"""<image href="{LICHESS_LOGO_DARK_MODE if colors['dark-mode'] else LICHESS_LOGO_LIGHT_MODE}" height="18" x="11" y="270"/>"""
            if platform_logo
            else ""
        )
        background_svg = (
            f"""<rect width="400" height="265" rx="5" ry="5" fill="{colors['bg']}" />"""
        )

        # Constants for element widths
        PATRON_WINGS_WIDTH = 25
        FLAIR_WIDTH = 25
        GAP = 5
        BOLD_WIDTH_MULTIPLIER = 1.05

        x_pos = 15  # base left margin

        # Patron wings (constant width)
        patron_wings_svg = ""
        if player_data["patron_wings_color"]:
            patron_wings_svg = f"""<path transform="scale(0.05, -0.05) translate({x_pos * 20}, -780)" d="M1 508q0 -1 0.5 -3t1 -5t0.5 -5q2 -35 21 -72q13 -27 35 -47q24 -24 57 -43t104 -49q68 -28 100 -47q41 -24 41 -28l-5 3q-6 2 -11 4q-34 10 -112 24q-101 18 -144 36q-28 12 -43 21q-8 5 -8 4q2 -5 4 -11q28 -73 110 -96q31 -8 108 -17q78 -7 108 -16l9 -3h-18 q-25 0 -70 -7q-55 -6 -82 -7q-39 -2 -82 8l-9 4q-1 -1 8.5 -13.5t16.5 -19.5q23 -23 57 -34q10 -2 34 -2q31 0 83 12q62 12 68 12q4 1 15 1l6 1l-9 -3q-26 -11 -50 -25q-60 -34 -103 -37l-13 -2l10 -8q21 -16 37 -22q3 -1 22 -5q19 -1 36 7t53 35q29 21 39 24q14 5 26 -1 q16 -9 16 -27v-4v-3v-2q-1 -2 -2 0l-1 3q-5 10 -15.5 13.5t-19.5 -2.5q-18 -9 -11 -29q1 -3 7 -11q14 -14 33 -13.5t32 15.5q25 24 7 54q-10 14 -20 18l-12 6q-14 11 -15 15q16 -5 32.5 2t23.5 23q10 22 -3 42q-11 20 -37 22q-13 0 -21 -5q-13 -11 -6 -24q8 -19 27 -12 q11 5 12 12q1 2 2 -5q-3 -18 -17 -26q-14 -6 -29 0q-8 5 -14 15q-3 12 -3 20q-6 31 -15 48q-15 32 -49 60q-36 29 -129 77q-90 47 -132 74.5t-76 63.5l-15 15q-1 0 -1 -3z" fill="{LICHESS_PATRONS_COLOR_MAP[player_data['patron_wings_color']]}" />"""
            x_pos += PATRON_WINGS_WIDTH + GAP

        # Title (variable width, bold)
        title_svg = ""
        if player_data["title"]:
            title_svg = f"""<text x="{x_pos}" y="25" fill="#b68335" font-family="Arial" font-weight="bold" font-size="16" dominant-baseline="hanging">{player_data["title"]}</text>"""
            title_width = (
                get_string_width(player_data["title"], 16) * BOLD_WIDTH_MULTIPLIER
            )
            x_pos += title_width + GAP

        # Username (variable width)
        username_svg = f"""<text x="{x_pos}" y="25" fill="{colors['text-bright']}" font-family="Arial" font-size="18" dominant-baseline="hanging">{player_data['username']}</text>"""
        x_pos += get_string_width(player_data["username"], 18) + GAP

        # Flair (constant width)
        flair_svg = ""
        if player_data["flair"]:
            flair_svg = f"""<image href="{LICHESS_FLAIRS[player_data['flair']]}" x="{x_pos}" y="17" width="{FLAIR_WIDTH}" />"""
            x_pos += FLAIR_WIDTH + GAP

        # Flag (constant width)
        country_svg = ""
        if player_data["country_code"]:
            country_svg = Lichess.generate_flag_svg(
                country_code=player_data["country_code"], x_pos=x_pos
            )

        joined_last_seen_and_time_spent_svg = f"""
            <text x="15" y="50" fill="{colors['text-light']}" font-family="Arial" font-size="10"
                dominant-baseline="hanging">
                <tspan>Joined:</tspan>
                <tspan fill="{colors['text-bright']}">{player_data['joined']}</tspan>
                <tspan>|</tspan>
                <tspan>Last seen:</tspan>
                <tspan fill="{colors['text-bright']}">{player_data['last_seen']}</tspan>
                <tspan>|</tspan>
                <tspan>Time spent:</tspan>
                <tspan fill="{colors['text-bright']}">{Lichess.normalize_time_spent(player_data["play_time"])}</tspan>
            </text>
        """

        bio_svg = ""
        if player_data["bio"]:
            bio_lines = Lichess.split_bio_text(
                player_data["bio"], font_size=10, max_width=375
            )
            if len(bio_lines) == 1:
                bio_svg = f"""<text x="15" y="82" fill="{colors['text-mid']}" font-family="Arial" font-size="10">{bio_lines[0]}</text>"""
            elif len(bio_lines) == 2:
                bio_svg = f"""<text x="15" y="75" fill="{colors['text-mid']}" font-family="Arial" font-size="10">{bio_lines[0]}</text><text x="15" y="90" fill="{colors['text-mid']}" font-family="Arial" font-size="10">{bio_lines[1]}</text>"""

        rapid_svg = f"""<rect x="10" y="100" width="120" height="150" fill="{colors['fg']}" rx="5" ry="5" /> <path transform="scale(0.06, -0.06) translate(475, -2300)" x="100" y="100" d="{LICHESS_TIME_RAPID_PATH}" fill="#A46E23" /> <text x="80" y="130" fill="{colors['text-bright']}" font-family="Arial" font-size="14" font-weight="" text-anchor="middle">Rapid</text> <text x="70" y="160" fill="{colors['text-bright']}" font-family="Arial" font-size="22" font-weight="bold" text-anchor="middle">{player_data['stats']['rapid']['last']}</text> <text x="70" y="185" fill="{colors['text-mid']}" font-family="Arial" font-size="12" text-anchor="middle"> Highest</text> <text x="70" y="200" fill="{colors['text-mid']}" font-family="Arial" font-size="14" text-anchor="middle">{player_data['stats']['rapid']['best']}</text> <text x="70" y="225" font-family="Arial" font-size="11" text-anchor="middle"> <tspan fill="{colors['win']}">{player_data['stats']['rapid']['wins']}</tspan> <tspan fill="{colors['text-mid']}">|</tspan> <tspan fill="{colors['draw']}">{player_data['stats']['rapid']['draws']}</tspan> <tspan fill="{colors['text-mid']}">|</tspan> <tspan fill="{colors['loss']}">{player_data['stats']['rapid']['losses']}</tspan> </text>"""

        blitz_svg = f"""<rect x="140" y="100" width="120" height="150" fill="{colors['fg']}" rx="5" ry="5" /> <path transform="scale(0.06, -0.06) translate(2700, -2300)" x="100" y="100" d="{LICHESS_TIME_BLITZ_PATH}" fill="#A46E23" /> <text x="208" y="130" fill="{colors['text-bright']}" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle">Blitz</text> <text x="200" y="160" fill="{colors['text-bright']}" font-family="Arial" font-size="22" font-weight="bold" text-anchor="middle">{player_data['stats']['blitz']['last']}</text> <text x="200" y="185" fill="{colors['text-mid']}" font-family="Arial" font-size="12" text-anchor="middle"> Highest</text> <text x="200" y="200" fill="{colors['text-mid']}" font-family="Arial" font-size="14" text-anchor="middle">{player_data['stats']['blitz']['best']}</text> <text x="200" y="225" font-family="Arial" font-size="11" text-anchor="middle"> <tspan fill="{colors['win']}">{player_data['stats']['blitz']['wins']}</tspan> <tspan fill="{colors['text-mid']}">|</tspan> <tspan fill="{colors['draw']}">{player_data['stats']['blitz']['draws']}</tspan> <tspan fill="{colors['text-mid']}">|</tspan> <tspan fill="{colors['loss']}">{player_data['stats']['blitz']['losses']}</tspan> </text>"""

        bullet_svg = f"""<rect x="270" y="100" width="120" height="150" fill="{colors['fg']}" rx="5" ry="5" /> <path transform="scale(0.06, -0.06) translate(4760, -2320)" x="100" y="100" d="{LICHESS_TIME_BULLET_PATH}" fill="#A46E23" /> <text x="340" y="130" fill="{colors['text-bright']}" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle">Bullet</text> <text x="330" y="160" fill="{colors['text-bright']}" font-family="Arial" font-size="22" font-weight="bold" text-anchor="middle">{player_data['stats']['bullet']['last']}</text> <text x="330" y="185" fill="{colors['text-mid']}" font-family="Arial" font-size="12" text-anchor="middle"> Highest</text> <text x="330" y="200" fill="{colors['text-mid']}" font-family="Arial" font-size="14" text-anchor="middle">{player_data['stats']['bullet']['best']}</text> <text x="330" y="225" font-family="Arial" font-size="11" text-anchor="middle"> <tspan fill="{colors['win']}">{player_data['stats']['bullet']['wins']}</tspan> <tspan fill="{colors['text-mid']}">|</tspan> <tspan fill="{colors['draw']}">{player_data['stats']['bullet']['draws']}</tspan> <tspan fill="{colors['text-mid']}">|</tspan> <tspan fill="{colors['loss']}">{player_data['stats']['bullet']['losses']}</tspan> </text>"""

        svg = "".join(
            [
                f"""<svg width="400" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">""",
                footer_section,
                platform_logo,
                background_svg,
                patron_wings_svg,
                title_svg,
                username_svg,
                flair_svg,
                country_svg,
                joined_last_seen_and_time_spent_svg,
                bio_svg,
                rapid_svg,
                blitz_svg,
                bullet_svg,
                """</svg>""",
            ]
        )

        return svg
