import base64


def utf8_encode(s):
    # 实现与JavaScript相同的UTF-8编码
    encoded = []
    i = 0
    while i < len(s):
        c = ord(s[i])
        if c < 0x80:
            encoded.append(c)
            i += 1
        elif c < 0x800:
            encoded.append(0xc0 | (c >> 6))
            encoded.append(0x80 | (c & 0x3f))
            i += 1
        elif 0xd800 <= c <= 0xdbff:
            if i + 1 < len(s):
                c2 = ord(s[i + 1])
                if 0xdc00 <= c2 <= 0xdfff:
                    c = 0x10000 + ((c & 0x3ff) << 10) + (c2 & 0x3ff)
                    encoded.append(0xf0 | (c >> 18))
                    encoded.append(0x80 | ((c >> 12) & 0x3f))
                    encoded.append(0x80 | ((c >> 6) & 0x3f))
                    encoded.append(0x80 | (c & 0x3f))
                    i += 2
                else:
                    raise ValueError("Malformed UTF-16 string")
            else:
                raise ValueError("Malformed UTF-16 string")
        else:
            encoded.append(0xe0 | (c >> 12))
            encoded.append(0x80 | ((c >> 6) & 0x3f))
            encoded.append(0x80 | (c & 0x3f))
            i += 1
    return bytes(encoded).decode('latin1')


def to_uint32(n):
    return n & 0xFFFFFFFF


def mx_function(z, y, sum, key, p, e):
    return ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) ^ ((sum ^ y) + (key[p & 3 ^ e] ^ z))


def str_to_words(s, include_length):
    length = len(s)
    words = []
    for i in range(0, length, 4):
        word = 0
        for j in range(4):
            if i + j < length:
                word |= ord(s[i + j]) << (j * 8)
        words.append(word)

    if include_length:
        words.append(length)

    return words


def words_to_bytes(words, include_length):
    byte_array = bytearray()
    for word in words:
        byte_array.append(word & 0xFF)
        byte_array.append((word >> 8) & 0xFF)
        byte_array.append((word >> 16) & 0xFF)
        byte_array.append((word >> 24) & 0xFF)

    if include_length:
        last_word = words[-1]
        if last_word < len(byte_array) - 3 or last_word > len(byte_array):
            return None
        byte_array = byte_array[:last_word]

    return bytes(byte_array)


def encrypt(data, key):
    if not data:
        return data

    # UTF-8编码
    data = utf8_encode(data)
    key = utf8_encode(key)

    # 转换为words数组
    data_words = str_to_words(data, True)
    key_words = str_to_words(key, False)

    # 确保key至少有4个元素
    while len(key_words) < 4:
        key_words.append(0)

    n = len(data_words) - 1
    if n < 1:
        return data

    # XXTEA加密
    z = data_words[n]
    y = data_words[0]
    sum = 0
    delta = 0x9E3779B9
    q = 6 + 52 // (n + 1)

    for _ in range(q):
        sum = to_uint32(sum + delta)
        e = (sum >> 2) & 3

        for p in range(n):
            y = data_words[p + 1]
            z = data_words[p] = to_uint32(data_words[p] + mx_function(z, y, sum, key_words, p, e))

        y = data_words[0]
        z = data_words[n] = to_uint32(data_words[n] + mx_function(z, y, sum, key_words, n, e))

    # 转换回字节并编码为Base64
    encrypted_bytes = words_to_bytes(data_words, False)
    return base64.b64encode(encrypted_bytes).decode('utf-8')
