# target: aHR0cHM6Ly9pLmVhc3Rtb25leS5jb20vd2Vic2l0ZWNhcHRjaGEvc2xpZGVydmFsaWQ=
import json
import math
import random
import re
import time
import requests
import numpy as np
from captcha_recognizer.recognizer import Recognizer
from io import BytesIO
from PIL import Image
import XXTEA_JS


def encryptXXTEA(plaintext: str) -> str:
    key = "e98ae8878c264a7e"
    encrypted_base64 = XXTEA_JS.encrypt(plaintext, key)
    return encrypted_base64


def genQgqp_b_id() -> str:
    # 生成一个 ID
    e = str(random.randint(1, 9))  # 第一个数字 1~9
    for _ in range(19):
        e += str(random.randint(0, 8))  # 后面跟随 19 个数字 0~8
    # 输出生成的 ID
    print(f"[+] Generated qgqp_b_id: {e}")
    return e


def getContextId() -> str:
    data1 = {"qgqp_b_id": qgqp_b_id}
    resp = requests.post(
        url="https://i.eastmoney.com/websitecaptcha/api/getcontextid",
        data=data1,
        headers=headers
    )
    d = json.loads(resp.text)["contextid"]
    print(f"[+] Get context_id: {d}")
    return d


def getImgInfo() -> str:
    fmt_data = f"appid=202503141611|ctxid={context_id}|a=quoteapi|p=|r={random.random()}"
    enc_data = encryptXXTEA(fmt_data)
    print(f"[+] 加密后的数据: {enc_data}")
    img_params = {
        "callback": "cb",
        "ctxid": context_id,
        "request": enc_data,
        "_": time.time() * 1000
    }
    img_resp = requests.get(
        url="https://smartvcode2.eastmoney.com/Titan/api/captcha/get",
        params=img_params,
        headers=headers
    )
    i = img_resp.text
    print(f"[+] 本次响应数据: {i}")
    return i


def genCompleteImg():
    # 数组a写死
    a = [39, 38, 48, 49, 41, 40, 46, 47, 35, 34, 50, 51, 33, 32, 28, 29, 27, 26, 36, 37, 31, 30, 44, 45, 43, 42, 12, 13,
         23, 22, 14, 15, 21, 20, 8, 9, 25, 24, 6, 7, 3, 2, 0, 1, 11, 10, 4, 5, 19, 18, 16, 17]
    bg_image = requests.get(url=bg_img, headers=headers).content
    # 背景图的高度为160
    height = 160
    image = Image.open(BytesIO(bg_image))
    slices = []
    # 模拟背景图切割过程
    for l in range(len(a)):
        # 计算横向偏移
        x_offset = a[l] % 26 * 12 + 0.4
        # 计算纵向偏移
        if a[l] <= 25:
            y_offset = height // 2
        else:
            y_offset = 0
        left = x_offset
        upper = y_offset
        right = left + 12
        lower = upper + 80
        # 裁剪图像并保存
        cropped_img = image.crop((left, upper, right, lower)).resize((10, 80), Image.Resampling.LANCZOS)
        slices.append(cropped_img)
    columns = 26
    rows = 2
    # 创建一张空白图像，大小为每个小块宽度 * 列数，高度 * 行数
    result_image = Image.new("RGB", (columns * 10, rows * 80))

    # 将切割的小块拼接到新图像中
    for i, slice_ in enumerate(slices):
        row = i // columns
        col = i % columns
        x_position = col * 10
        y_position = row * 80
        # 将切割图像粘贴到拼接图像的指定位置
        result_image.paste(slice_, (x_position, y_position))

    # 保存拼接后的图像
    result_image.save("3_combined_image.jpg")


def getDistance() -> int:
    recognizer = Recognizer()
    box, confidence = recognizer.identify_gap(source="./3_combined_image.jpg", is_single=True, verbose=False)
    box_x = box[0]
    d = int(box_x - 8)
    return d


def formatTraceWithTime(points, total_time=1500, enable_shake=True, enable_tail_slow=True):
    if not points or len(points) < 2:
        return "", 0

    # 计算各段长度
    distances = []
    total_distance = 0
    for i in range(1, len(points)):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        d = math.hypot(x2 - x1, y2 - y1)
        distances.append(d)
        total_distance += d

    trace = []
    t = 0
    x, y = points[0]
    trace.append(f"{int(x)},{int(y)},{t}")

    for i in range(1, len(points)):
        x, y = points[i]
        segment_time = int((distances[i - 1] / total_distance) * total_time)
        t += segment_time

        # 模拟轻微抖动（小幅度 ±1px 偏移）
        if enable_shake and i < len(points) - 1:
            x += random.choice([-1, 0, 1])
            y += random.choice([-1, 0, 1])

        trace.append(f"{int(x)},{int(y)},{t}")

    # 模拟缓冲减速（最后多几个点，慢速）
    if enable_tail_slow:
        last_x, last_y = points[-1]
        for dx in [1, -1, 1]:  # 缓慢左右移动
            t += random.randint(80, 120)
            trace.append(f"{int(last_x + dx)},{int(last_y)},{t}")

    return ":".join(trace), t


def genSliderTrace():
        def cubic_bezier_curve(x1, y1, x2, y2, x_cp1=1, y_cp1=2, x_cp2=2, y_cp2=-1, num_points=20):
            # 生成一个从0到1的数列，用于计算贝塞尔曲线上的点
            t = np.linspace(0, 1, num_points)
            points = []

            # 遍历参数t的每个值，计算曲线上对应点的坐标
            for t_val in t:
                # 三次贝塞尔曲线的公式
                x = np.power((1 - t_val), 3) * x1 + 3 * np.power((1 - t_val), 2) * t_val * x_cp1 + \
                    3 * (1 - t_val) * np.power(t_val, 2) * x_cp2 + np.power(t_val, 3) * x2
                y = np.power((1 - t_val), 3) * y1 + 3 * np.power((1 - t_val), 2) * t_val * y_cp1 + \
                    3 * (1 - t_val) * np.power(t_val, 2) * y_cp2 + np.power(t_val, 3) * y2

                # 将计算得到的点添加到列表中
                points.append((x, y))

            # 返回曲线上所有计算得到的点
            return points

        x1, y1 = 0, 0
        # 目标点
        x2, y2 = distance, -1

        t = cubic_bezier_curve(x1, y1, x2, y2, x_cp1=40, y_cp1=20, x_cp2=240, y_cp2=160)
        return t


def passVerify():
    fmt_data = f"appid=202503141611|ctxid={context_id}|type=slide|u={distance}|d={traces}|a=quoteapi|p" \
               f"=|t={t_time}|r={random.random()}"
    print(f"[+] 验证数据: {fmt_data}")
    enc_data = encryptXXTEA(fmt_data)
    v_params = {
        "callback": "cb",
        "ctxid": context_id,
        "request": enc_data,
        "_": time.time() * 1000
    }
    v_resp = requests.get(
        url="https://smartvcode5.eastmoney.com/Titan/api/captcha/Validate",
        params=v_params,
        headers=headers
    )
    print(f"[+] 结果: {v_resp.text}")


if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/138.0.0.0"
                      "Safari/537.36",
        "Referer": "https://i.eastmoney.com/websitecaptcha/slidervalid",
        "Content-Type": "text/plain;charset=UTF-8",
        "Sec-Ch-Ua-Platform": "Windows",
        "Accept": "*/*"
    }
    qgqp_b_id = genQgqp_b_id()
    context_id = getContextId()
    getImgInfo()
    info = getImgInfo()
    # 提取 JSON 部分
    json_str = re.search(r'cb\((\{.*\})\);', info).group(1)
    data = json.loads(json_str)
    captcha_info = data["Data"]["CaptchaInfo"]
    captcha_info_dict = json.loads(captcha_info)
    # 提取 bg 和 slice
    static_servers = captcha_info_dict["static_servers"][0]
    bg_img = "https://" + static_servers + captcha_info_dict["bg"]
    slice_img = "https://" + static_servers + captcha_info_dict["slice"]
    print(f"[+] 背景图链接: {bg_img}")
    print(f"[+] 滑块图链接: {slice_img}")
    genCompleteImg()
    distance = getDistance()
    print(f"[+] 滑动距离: {distance}")
    traces, t_time = formatTraceWithTime(genSliderTrace())
    passVerify()
