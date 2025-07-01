# target: aHR0cHM6Ly92OC5jaGFveGluZy5jb20v
import hashlib
import io
import json
import re
import time
import requests
import uuid

from PIL import Image, ImageDraw
from ddddocr import DdddOcr


def getTimestamp() -> str:
    return str(int(time.time() * 1000))


def getUUID():
    u = uuid.uuid4()
    return str(u)


def getMD5(input_str: str) -> str:
    res = hashlib.md5(input_str.encode('utf-8')).hexdigest()
    return res


# 获取服务器返回时间
def getServerTime() -> str:
    params1 = {
        'callback': 'cx_captcha_function',
        'captchaId': captchaId,
        '_': int(now_time),
    }
    response1 = requests.get("https://captcha.chaoxing.com/captcha/get/conf", params=params1, headers=headers).text
    res = re.findall(r'cx_captcha_function\((.*)\)', response1)
    return str(json.loads(res[0])['t'])


# 获取图片地址和验证token
def getVerifyParams() -> (str, str, str, str):
    server_time = getServerTime()
    print(f"[+] 获取到的服务器时间: {server_time}")

    # 先计算captchaKey
    captchaKey = getMD5(server_time + getUUID())
    print(f"[+] 计算得到的captchaKey: {captchaKey}")
    # 再计算token
    c_token = getMD5(server_time + captchaId + "slide" + captchaKey) + ':' + str(int(server_time) + 300000)
    print(f"[+] 计算得到的c_token: {c_token}")
    # 最后计算iv
    iv = getMD5(captchaId + "slide" + now_time + getUUID())
    print(f"[+] 计算得到的iv: {iv}")

    params = {
        "callback": "cx_captcha_function",
        "captchaId": captchaId,
        "type": "slide",
        "version": "1.1.20",
        "captchaKey": captchaKey,
        "token": c_token,
        "referer": "https://v8.chaoxing.com/",
        "iv": iv,
        "_": int(now_time) + 2
    }

    response = requests.get(
        url="https://captcha.chaoxing.com/captcha/get/verification/image",
        params=params,
        headers=headers,
        cookies=cookies
    ).text
    # 提取 JSON 内容
    json_data = json.loads(re.search(r'cx_captcha_function\((\{.*\})\)', response).group(1))
    v_token = json_data["token"]
    shade_image = json_data["imageVerificationVo"]["shadeImage"]
    cutout_image = json_data["imageVerificationVo"]["cutoutImage"]
    print(f"[+] 获取得到的用于验证的v_token: {v_token}")
    print(f"[+] 获取得到的背景图片地址: {shade_image}")
    print(f"[+] 获取得到的滑块图片地址: {cutout_image}")
    return iv, v_token, shade_image, cutout_image


# 计算得到滑动距离
def getDistance(save_path="2_temp_rsult.jpg") -> (str, int):
    iv, v_token, shade_image, cutout_image = getVerifyParams()
    bg_image = requests.get(url=shade_image, cookies=cookies, headers=headers).content
    slice_image = requests.get(cutout_image, cookies=cookies, headers=headers).content
    det = DdddOcr(det=False, ocr=False, show_ad=False)
    res = det.slide_match(slice_image, bg_image, simple_target=True)
    if save_path is not None:
        # 将背景图片的二进制数据加载为Pillow Image对象
        left, top, right, bottom = res['target'][0], res['target'][1], res['target'][2], res['target'][3]
        bg_image = Image.open(io.BytesIO(bg_image))
        draw = ImageDraw.Draw(bg_image)
        draw.rectangle([left, top, right, bottom], outline="red", width=2)
        bg_image.save("2_temp_rsult.jpg")
        print(f"[+] 已保存标注后的图片到: {save_path}")
        return iv, v_token, res["target"][0]
    return res


def passVerify():
    iv, v_token, distance = getDistance()
    # 模拟滑动轨迹等参数（举例）
    params = {
        "callback": "cx_captcha_function",
        "captchaId": captchaId,
        "type": "slide",
        "token": v_token,
        "textClickArr": '[{"x":' + str(distance) + '}]',
        "coordinate": '[]',
        "runEnv": "10",
        "version": "1.1.20",
        "t": "a",
        "iv": iv,
        "_": now_time
    }
    response = requests.get(
        url="https://captcha.chaoxing.com/captcha/check/verification/result",
        cookies=cookies,
        headers=headers,
        params=params
    ).text
    print(f"[+] 验证结果: {response}")


if __name__ == "__main__":
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/138.0.0.0"
                      "Safari/537.36",
        "Referer": "https://v8.chaoxing.com/",
        "Content-Type": "text/plain;charset=UTF-8",
        "Sec-Ch-Ua-Platform": "Windows",
        "Accept": "*/*"
    }
    # 获取服务器返回的 cookie（字典格式）
    cookies = requests.get(url="https://v8.chaoxing.com/", headers=headers).cookies.get_dict()
    captchaId = "qDG21VMg9qS5Rcok4cfpnHGnpf5LhcAv"
    now_time = getTimestamp()
    passVerify()
