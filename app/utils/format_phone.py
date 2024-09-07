def format_phone(phone_str):
    ddd = phone_str[:2]
    first_digit = phone_str[2]
    rest_of_number = phone_str[3:]

    return f"({ddd}) {first_digit}{rest_of_number[:4]}-{rest_of_number[4:]}"
