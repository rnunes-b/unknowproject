from datetime import datetime


def format_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    return date_obj.strftime("%d/%m/%Y")
