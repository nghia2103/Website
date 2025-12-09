def format_currency(value):
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return "{:,.0f}".format(value).replace(',', '.')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS