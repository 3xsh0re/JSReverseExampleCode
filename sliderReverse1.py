import io
import random
import re
import json
import asyncio
import secrets
import string

import requests
import websockets
import time

from PIL import Image, ImageDraw
from bs4 import BeautifulSoup
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Util import Counter
from ddddocr import DdddOcr

plain_text_1 = "{\"requestId\":\"timestamp\",\"command\":\"7051CA8BF3E64DEDAA9334620DA8F5F1\",\"data\":{" \
             "\"l\":\"token\",\"f\":\"43b18dd09497378a6413ca595b0c9b4e577ccc6c\"," \
             "\"m\":\"148ed959d11747ccacab96436abfb63a\",\"j\":\"ES5\"," \
             "\"tl\":5,\"o\":{\"spm\":\"148ed959d11747ccacab96436abfb63a\"," \
             "\"v5lid\":\"XAZsqZXc9wBlyS4Wb4nimDUMjR2A5xUp\",\"userAgent\":" \
             "\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36\"," \
             "\"language\":\"en-US\",\"colorDepth\":24,\"deviceMemory\":8,\"pixelRatio\":1," \
             "\"hardwareConcurrency\":12,\"screenResolution\":[1920,1080],\"availableScreenResolution\":[1032,1920]," \
             "\"timezoneOffset\":-480," \
             "\"timezone\":\"Asia/Shanghai\"," \
             "\"platform\":\"Win32\",\"canvas\":\"d1034063356f4ad08595c77be66f615b1cd68ad2\"," \
             "\"webgl\":\"631d07d370a482e4b150f953655b7b0307a372fc\",\"touchSupport\":[10,false,false]," \
             "\"audio\":\"124.04347527516074\",\"j\":\"ES5\"},\"exfp\":{\"fpa\":\"902f0fe98719b779ea37f27528dfb0aa\"," \
             "\"fphc\":\"d1034063356f4ad08595c77be66f615b1cd68ad2\"," \
             "\"fphg\":\"631d07d370a482e4b150f953655b7b0307a372fc\"," \
             "\"fphf\":\"43b18dd09497378a6413ca595b0c9b4e577ccc6c\"," \
             "\"fprt\":\"818fd83993ffb81fe8313bc22aad3797e45dd6b3\"},\"aux\":{\"k\":[],\"m\":[[3,126,711,3287],[3,126," \
             "710,3290]," \
             "[3,126,709,3292],[3,126,708,3296],[3,125,708,3299],[3,125,707,3301],[3,125,706,3305],[3,125,705,3309]," \
             "[3,125,704,3315],[3,124,704,3316],[3,124,703,3323],[3,124,702,3327],[3,124,701,3332],[3,123,701,3339],[3," \
             "123,700,3345],[3,123,699,3350],[3,123,698,3353],[3,123,697,3357],[1,123,697,3379],[2,123,697,3443]]," \
             "\"h\":[[3,145,0,611],[3,145,1,612],[3,147,2,613],[3,148,3,614],[3,149,4,615],[3,150,5,616],[3,151,6,617]," \
             "[3,152,7,618],[3,153,8,619],[3,155,9,620],[3,156,9,621],[3,157,10,622],[3,159,12,623],[3,160,13,624],[3," \
             "162,14,625],[3,163,15,626],[3,164,16,627],[3,166,16,629],[3,167,18,630],[3,168,19,631]]}}}"
plain_text_2 = "{\"requestId\":\"timestamp\",\"command\":\"E97CE473AE1A46A8BF4A88FD73636D7E\"," \
               "\"data\":{\"l\":\"token\"," \
               "\"z\":\"43b18dd09497378a6413ca595b0c9b4e577ccc6c\"}}"
plain_text_3 = "{\"requestId\":\"timestamp\",\"command\":" \
               "\"53031DCA131946D78173670CE98E8812\",\"data\":{\"s\":\"moveData\"," \
               "\"f\":\"43b18dd09497378a6413ca595b0c9b4e577ccc6c\"}}"
cmd_1 = "7051CA8BF3E64DEDAA9334620DA8F5F1"
cmd_2 = "E97CE473AE1A46A8BF4A88FD73636D7E"
cmd_3 = "53031DCA131946D78173670CE98E8812"


def getToken(url: str):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # 找到含有 v5-config 属性的 div
    target_div = soup.find('div', attrs={'v5-config': True})
    config_str = target_div['v5-config']

    # 用正则提取 token
    match = re.search(r"token:'([a-fA-F0-9]{32})'", config_str)
    if match:
        token = match.group(1)
        print("[+] 提取到的token:", token)
        return token
    else:
        print("[-] 未找到token")


def genKey(intput_str: str, b: str):
    key = ""
    b = ord(b[-1]) % 2
    for i in range(b, len(intput_str), 2):
        key += intput_str[i]
    return key


def genEncIV() -> str:
    charset = string.ascii_letters + string.digits  # 包括 a-zA-Z0-9
    iv = ''.join(secrets.choice(charset) for _ in range(16))
    return iv


def encrypt(plaintext: str, key: str, iv: str) -> str:
    plaintext = plaintext.encode('utf-8')
    key = key.encode('utf-8')
    iv = iv.encode('utf-8')

    iv_int = int.from_bytes(iv, byteorder='big')
    # 创建一个计数器对象, 初始向量为16个字节
    ctr = Counter.new(128, initial_value=iv_int)

    # 创建AES-CTR加密器
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)

    # 加密明文
    ciphertext = cipher.encrypt(plaintext)
    encrypted = iv + ciphertext

    return b64encode(encrypted).decode('utf-8')


def decrypt(ciphertext: str, key: str) -> str:
    # 1. Base64解码输入密文
    decoded = b64decode(ciphertext).hex()
    iv = bytes.fromhex(decoded[:32])  # 前32位hex字符作为IV
    cipher_text = b64encode(bytes.fromhex(decoded[32:])).decode('utf-8')

    # 2. 初始化CTR模式
    iv_int = int.from_bytes(iv, byteorder='big')
    ctr = Counter.new(128, initial_value=iv_int)

    # 3. 创建AES-CTR解密器
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CTR, counter=ctr)

    # 4. 解密并尝试解码为UTF-8字符串
    decrypted = cipher.decrypt(b64decode(cipher_text))
    try:
        return decrypted.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("Token is wrong or expired.")


# 分割字符串
def chunkStr(enc_str: str):
    chunk_size = 1024
    split_enc_str = []
    for i in range(0, 3):
        split_enc_str.append(f"0|3|{i}|" + enc_str[i * chunk_size: (i + 1) * chunk_size])
    return split_enc_str


def getDistance(bg, tp, save_path=None):
    det = DdddOcr(det=False, ocr=False, show_ad=False)
    res = det.slide_match(tp, bg, simple_target=True)
    if save_path is not None:
        # 将背景图片的二进制数据加载为Pillow Image对象
        left, top, right, bottom = res['target'][0], res['target'][1], res['target'][2], res['target'][3]
        bg_image = Image.open(io.BytesIO(bg))
        draw = ImageDraw.Draw(bg_image)
        draw.rectangle([left, top, right, bottom], outline="red", width=2)
        bg_image.save(save_path)
        print(f"[+] 已保存标注后的图片到: {save_path}")
        return res
    return res


def generateSliderTrack(target_distance):
    track = []
    start_time = int(time.time() * 1000)
    current_distance = 0
    current_time = 0

    track.extend([str(start_time)])
    while current_distance < target_distance:
        # 时间步长随机，模拟不均匀采样，25~65ms之间
        time_step = random.randint(25, 65)
        current_time += time_step

        # 横向步长，接近目标时减小步长
        if target_distance - current_distance > 10:
            x_step = random.randint(4, 10)
        else:
            x_step = random.randint(1, 4)

        current_distance += x_step
        if current_distance > target_distance:
            current_distance = target_distance

        # 纵向浮动在-4到4之间，模拟抖动
        y_offset = random.randint(-4, 4)

        track.extend([str(current_time), str(current_distance), str(y_offset)])

    end_date = start_time + current_time + random.randint(100, 500)
    track.extend([str(end_date)])
    track_str = ",".join(track)
    return track_str, str(start_time)


async def communicate(this_token):
    uri = "wss://rm0w8a6ckkco.verify5.com/api"
    async with websockets.connect(uri) as ws:
        print("[+] 已连接到rm0w8a6ckkco.verify5.com")
        req_id = "Req_" + str(int(time.time() * 10000))

        # 第一次发送消息
        send_msg_1 = plain_text_1.replace("timestamp", req_id).replace("token", this_token)
        print(f"[+] 第一次发送消息明文: {send_msg_1}")
        enc_text_1 = encrypt(send_msg_1, genKey(this_token, this_token), genEncIV())
        print(f"[+] 第一次发送消息密文: {enc_text_1}")
        chunk_msg_1 = chunkStr(cmd_1 + this_token + enc_text_1)
        for i in range(len(chunk_msg_1)):
            await ws.send(chunk_msg_1[i])
            print(f"[+] 已发送: {chunk_msg_1[i]}")

        recv_data_1 = []
        while len(recv_data_1) < 3:
            resp = await asyncio.wait_for(ws.recv(), timeout=5)  # 最多等5秒
            recv_data_1 += resp
        recv_data_1 = "".join(recv_data_1)
        print("[+] 第一次消息发送完成")
        print(f"[+] 第一次接受消息密文: {recv_data_1}")
        dec_data_1 = decrypt(recv_data_1[32:], genKey(recv_data_1[:32], this_token))
        print(f"[+] 第一次接受消息明文: {dec_data_1}")

        # 第二次发送消息
        send_msg_2 = plain_text_2.replace("timestamp", req_id).replace("token", this_token)
        print(f"[+] 第二次发送消息明文: {send_msg_2}")
        enc_text_2 = encrypt(send_msg_2, genKey(recv_data_1[:32], this_token), genEncIV())
        print(f"[+] 第二次发送消息密文: {enc_text_2}")
        recv_data_2 = []
        send_msg_2 = "1|1|0|" + cmd_2 + enc_text_2
        await ws.send(send_msg_2)
        print(f"[+] 已发送: {send_msg_2}")
        print("[+] 第二次消息发送完成")
        resp = await asyncio.wait_for(ws.recv(), timeout=5)  # 最多等5秒
        recv_data_2.append(resp)
        recv_data_2 = "".join(recv_data_2)
        print(f"[+] 第二次接收消息密文: {recv_data_2}")
        dec_data_2 = decrypt(recv_data_2, genKey(recv_data_1[:32], this_token))
        print(f"[+] 第二次接受消息明文: {dec_data_2}")

        # 第三次发送消息, 进行滑块操作
        j = json.loads(dec_data_2)
        pic_addr = [j["data"]['b'], j["data"]['s']]
        bg_image = requests.get(pic_addr[0]).content
        slice_image = requests.get(pic_addr[1]).content
        res = getDistance(bg_image, slice_image, "./temp_result.jpg")
        dis, n_time = generateSliderTrack(res['target'][0])

        req_id = "Req_" + n_time + "1"  # 重新获取时间戳
        send_msg_3 = plain_text_3.replace("timestamp", req_id).replace("moveData", dis)
        print(f"[+] 第三次发送消息明文: {send_msg_3}")
        enc_text_3 = encrypt(send_msg_3, genKey(recv_data_1[:32], this_token), genEncIV())
        print(f"[+] 第三次发送消息密文: {enc_text_3}")
        recv_data_3 = []
        send_msg_3 = "2|1|0|" + cmd_3 + enc_text_3
        await ws.send(send_msg_3)
        print(f"[+] 已发送: {send_msg_3}")
        print("[+] 第三次消息发送完成")
        resp = await ws.recv()
        recv_data_3.append(resp)
        recv_data_3 = "".join(recv_data_3)
        print(f"[+] 第三次接收消息密文: {recv_data_3}")
        dec_data_3 = decrypt(recv_data_3, genKey(recv_data_1[:32], this_token))
        print(f"[+] 第三次接受消息明文: {dec_data_3}")


if __name__ == '__main__':
    t_token = getToken("https://www.verify5.com/demo")
    asyncio.run(communicate(t_token))
