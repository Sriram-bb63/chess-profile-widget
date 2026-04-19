import copy
import datetime

from .constants_and_b64_assets import *


def convert_epoch_to_month_year(timestamp, unit="s"):
    if unit == "ms":
        timestamp = timestamp / 1000
    dt_obj = datetime.datetime.fromtimestamp(timestamp)
    dt_month_year = dt_obj.strftime("%b, %Y")
    return dt_month_year


def format_last_online(timestamp, unit="s"):
    if unit == "ms":
        timestamp = timestamp / 1000
    dt_obj = datetime.datetime.fromtimestamp(timestamp)
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    if dt_obj.date() == today.date():
        return "Today"
    elif dt_obj.date() == yesterday.date():
        return "Yesterday"
    elif dt_obj.year == today.year and dt_obj.month == today.month:
        return "This month"
    else:
        return convert_epoch_to_month_year(timestamp=timestamp)


def convert_secs_to_hours_mins(secs):
    hours = secs // 3600
    mins = (secs % 3600) // 60
    return hours, mins


def generate_flag_svg(country_code):
    if country_code not in FLAG_COORDINATES.keys():
        return ""
    return f"""<svg x="58" y="65" width="32" height="32" viewBox="0 0 32 24" overflow="hidden"> <image href="{FLAGS_PNG_B64}" x="{FLAG_COORDINATES[country_code][0]}" y="{FLAG_COORDINATES[country_code][1]}"></image> </svg>"""


def get_string_width(text, font_size):
    string_width = (
        sum([ARIAL_CHAR_WIDTH.get(ch, ARIAL_DEFAULT_CHAR_WIDTH) for ch in text])
        * font_size
    )
    return string_width


def fit_username(username, font_size, max_width):

    if get_string_width(username, font_size) <= max_width:
        return username

    low, high = 0, len(username)
    best_fit_username = ""
    while low <= high:
        mid = (low + high) // 2
        curr_username_candidate = username[:mid] + "..."
        if get_string_width(curr_username_candidate, font_size) <= max_width:
            best_fit_username = curr_username_candidate
            low = mid + 1
        else:
            high = mid - 1

    return best_fit_username
