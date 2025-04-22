import base62

SHORT_URL_LENGTH = 8

def shortener(counter: int) -> str:
    """
    Generate a short 8-character URL from the primary key counter of the database entry.
    This guarantees uniqueness for upto 218340105584895 ('zzzzzzzz' in base-62) distinct entries.

    short = leftpad(base62.encode(counter), 0)

    :param counter: The primary key counter of the database entry.
    :return: A short URL string of fixed length SHORT_URL_LENGTH.
    """

    assert(counter >= 0 and counter <= 218340105584895), "counter out of range"

    b62 = base62.encode(counter)
    if len(b62) < SHORT_URL_LENGTH:
        b62 = b62.zfill(SHORT_URL_LENGTH)
    elif len(b62) > SHORT_URL_LENGTH:
        b62 = b62[:SHORT_URL_LENGTH]
    return b62

def invshortener(short_url: str) -> int:
    """
    Decode a short URL back to the primary key counter of the database entry.

    This is the inverse of `shortener` and the counter can be used for fast
    indexed querying of the database.

    :param short_url: The short URL string.
    :return: The primary key counter of the database entry.
    """

    assert(len(short_url) == SHORT_URL_LENGTH), "short_url length mismatch"

    short_url = short_url.lstrip('0')
    if len(short_url) == 0:
        return 0

    return base62.decode(short_url)
