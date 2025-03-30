import cv2
import numpy as np
import keyboard
import threading
import time
import win32api
import win32con
import win32gui
import win32ui
import pyautogui
from PIL import Image, ImageGrab
import json
import random
import re
import pytesseract
import os

# --- 虚拟键码 ---
KEY_CODES = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
    'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F,
    'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59,
    'Z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'ESC': win32con.VK_ESCAPE,
    'SPACE': win32con.VK_SPACE,
    'F1': win32con.VK_F1,
    'F2': win32con.VK_F2,
    'F3': win32con.VK_F3,
    'F4': win32con.VK_F4,
    'F5': win32con.VK_F5,
    'F6': win32con.VK_F6,
    'F7': win32con.VK_F7,
    'F8': win32con.VK_F8,
    'F9': win32con.VK_F9,
    'F10': win32con.VK_F10,
    'F11': win32con.VK_F11,
    'F12': win32con.VK_F12
}

# --- 初始化 ---
hwnd = win32gui.FindWindow(None, "Legends Of Idleon")
lua = win32gui.FindWindow(None, "Lua Engine IDLEON-COPY")

# 获取游戏窗口大小
left, top, right, bottom = win32gui.GetWindowRect(hwnd)
game_width = right - left
game_height = bottom - top

running = True  # 控制脚本运行的标志

def load_config(config_path):
    """加载配置文件"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {config_path} 未找到！")
        return None
    except json.JSONDecodeError:
        print(f"配置文件 {config_path} 格式错误！")
        return None

config = load_config("config.json")
if config is None:
    exit()  # 如果加载配置失败，则退出程序

# --- 函数定义 ---

def find_image(image_path):
    """查找图像"""
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        game_width = right - left
        game_height = bottom - top
        game_area = (left, top, right, bottom)

        hdc = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hdc)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, game_width, game_height)

        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (game_width, game_height), mfcDC, (0, 0), win32con.SRCCOPY)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        screenshot = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)

        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) # 转换为灰度图像

        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE) # 将模板图像转换为灰度图像
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED) # 执行模板匹配
        _, max_val, _, max_loc = cv2.minMaxLoc(result) # 查找最大值和最小值及其位置

        if max_val >= THRESHOLD:
            return max_loc 
        else:
            return None

    except Exception as e:
        print(f"图像识别出错: {e}")
        return None

def click_and_hold(window, x, y, duration=0, click_times=1):
    """在指定窗口点击并按住指定时间, 使用模拟点击"""
    lParam = win32api.MAKELONG(x, y)
    for _ in range(click_times):
        start_time = time.time()
        while time.time() - start_time < duration:  
            win32api.PostMessage(window, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)  
            time.sleep(0.01)  
        win32api.PostMessage(window, win32con.WM_LBUTTONUP, 0, lParam) 
        if click_times > 1:
            time.sleep(0.1) 

def find_and_interact_image(image_path, area=None, duration=0, refresh=False, click_times=1, swipe=False, x_offset=0, y_offset=0, delay=0):
    """查找图像并执行交互操作，只在游戏窗口内进行，使用模拟点击"""
    threshold = 0.8
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        game_area = (left, top, right, bottom)

        if area is not None:
            area = (game_area[0] + area[0], game_area[1] + area[1], area[2], area[3])
        else:
            area = game_area

        hdc = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hdc)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, game_width, game_height)

        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (game_width, game_height), mfcDC, (0, 0), win32con.SRCCOPY)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        screenshot = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hdc)

        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            if image_path == config["breeding"]["breed_image"]:
                return find_and_interact_image(config["breeding"]["breed_01_image"])
            else:
                center_x = area[0] + max_loc[0] + template.shape[1] // 2
                center_y = area[1] + max_loc[1] + template.shape[0] // 2
            
            if swipe:
                 swipe_loot(hwnd, center_x, center_y - 50, 600, 10)
            elif refresh:
                click_and_hold(hwnd, *REFRESH_COORDINATES, duration=0.3)
                for _ in range(click_times):
                    click_and_hold(hwnd, center_x + x_offset, center_y + y_offset, duration)
                    time.sleep(delay)
            else:
                for _ in range(click_times):
                    click_and_hold(hwnd, center_x + x_offset, center_y + y_offset, duration)
                    time.sleep(delay)                    
            return True
        else:
            return False
    except Exception as e:
        print(f"图像识别出错: {e}")
        return False

def swipe_loot(hwnd, center_x, center_y, width, steps):
    """使用 PostMessage 模拟平滑的鼠标左右滑动"""
    start_x = center_x - width // 2
    end_x = center_x + width // 2

    x_step = (end_x - start_x) / steps

    lParam_start = win32api.MAKELONG(start_x, center_y)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam_start)

    for i in range(1, steps + 1):
        x = int(start_x + i * x_step)
        lParam = win32api.MAKELONG(x, center_y)
        win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParam)
        time.sleep(0.01)

    lParam_end = win32api.MAKELONG(end_x, center_y)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam_end)

def exit_handler():
    """监听 'delete' 键退出脚本"""
    global running
    while True:
        if keyboard.is_pressed('delete'):
            print("检测到 'delete' 键，退出脚本")
            running = False
            break

def press_key(key):
    """模拟按键按下和释放，并打印按键信息"""
    vk_code = key
    if isinstance(key, str):
        vk_code = KEY_CODES[key]

    #print(f"按下按键: {chr(vk_code)} (虚拟键码: {vk_code})")

    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
    time.sleep(0.2)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)

# --- 功能函数 ---

def afk_loop(config):
    """AFK 刷怪循环"""
    afk_config = config.get("afk")  # 获取 AFK 部分的配置
    if afk_config is None:
        print("AFK 配置未找到！")
        return
    while running:
        click_and_hold(hwnd, *afk_config["candy_position"], duration=0.3)
        time.sleep(0.7)
        
        find_and_interact_image(afk_config["claim_image"])
        time.sleep(0.5)
        
        find_and_interact_image(afk_config["gt_leg_image"], swipe=True)
        time.sleep(0.2)
        
        click_and_hold(hwnd, *afk_config["item_position"])
        time.sleep(0.5)

def afk_splice_loop():
    """AFK 合成循环"""
    while running:
        click_and_hold(hwnd, *AFK_CANDY_POSITION, duration=0.3)
        time.sleep(0.7)

        find_and_interact_image(AFK_GAIN_IMAGE, x_offset=-100)
        time.sleep(0.5)

        find_and_interact_image(AFK_CLAIM_IMAGE)
        time.sleep(0.5)
        
        find_and_interact_image(GT_LEG_IMAGE, swipe=True)
        time.sleep(0.2)
        
        click_and_hold(hwnd, *ITEM_POSITION)
        time.sleep(0.5)

def sailing_loop():
    """航海循环"""
    while running:
        click_and_hold(hwnd, *ITEM_POSITION)
        time.sleep(0.2)

        find_and_interact_image(SAILING_BOOST_IMAGE, duration=0.3)
        time.sleep(0.2)

        press_key('ESC')
        time.sleep(0.2)
        
        press_key('W')
        time.sleep(0.2)

        press_key('SPACE')
        time.sleep(4.5)
        
        press_key('ESC')
        time.sleep(0.5)
        
        click_and_hold(hwnd, *SAILING_TREASURE_POSITION)
        time.sleep(0.1)

        for _ in range(6):
            click_and_hold(hwnd, *SAILING_CHEST_POSITION, duration=0.2)

def postman_loop():
    """邮差循环"""
    while running:
        find_and_interact_image(POSTMAN_IMAGE, refresh=True)
        time.sleep(0.2)

        find_and_interact_image(POSTMAN_SIGN_IMAGE)
        time.sleep(0.2)

def dungeon_lootroll_loop():
    """地牢骰子循环"""
    while running:
        if find_and_interact_image(DUNGEON_LOOTROLL_IMAGE):
            continue

        click_and_hold(hwnd, *ITEM_POSITION)
        time.sleep(0.2)

        find_and_interact_image(DUNGEON_DICE_IMAGE, duration=0.3)
        press_key('ESC')

def breeding_loop():
    """养殖循环"""

    print("请选择要养殖的宠物：")
    choice = input("请输入选项: ")

    if choice not in BREEDING_PET_IMAGES:
        print("无效选项！")
        return

    pet_image_path = BREEDING_PET_IMAGES[choice]
    
    print("是否孵化闪光形态？")
    print("1. 是")
    print("2. 否")
    shiny_choice = input("请输入选项 (1-2): ")

    breed_shiny = True if shiny_choice == "1" else False
    
    print("请选择操作：")
    print("1. KEEP")
    print("2. TRASH")
    action_choice = input("请输入选项 (1-2): ")

    if action_choice == "1":
        action_image = KEEP_IMAGE
    elif action_choice == "2":
        action_image = TRASH_IMAGE
    else:
        print("无效选项！")
        return

    while running:
        press_key('W')
        time.sleep(0.2)

        press_key('SPACE')
        time.sleep(0.5)

        find_and_interact_image(pet_image_path)
        time.sleep(0.2)
        
        if breed_shiny:
            find_and_interact_image(BREED_SHINY_FORM)
            time.sleep(0.2)

        while find_and_interact_image(BREED_IMAGE):
            time.sleep(0.2)
            find_and_interact_image(action_image)
            time.sleep(0.2)

        click_and_hold(hwnd, *ITEM_POSITION)
        time.sleep(0.2)

        find_and_interact_image(EGG_IMAGE, duration=0.5)
        time.sleep(0.2)

        press_key('ESC')
        time.sleep(0.2)

def gaming_loop():
    """游戏循环"""
    while running:
        click_and_hold(hwnd, *ITEM_POSITION)
        time.sleep(0.2)

        find_and_interact_image(GAME_BOOST_IMAGE, duration=0.3)
        time.sleep(0.2)

        press_key('ESC')
        time.sleep(0.2)

        press_key('C')
        time.sleep(0.2)

        click_and_hold(hwnd, *QUIK_REF_POSITION, duration=0.2)
        time.sleep(0.5)

        click_and_hold(hwnd, *GAME_PC_POSITION, duration=0.2)
        time.sleep(0.5)
        
        click_and_hold(hwnd, *GAME_HARVEST_POSITION, duration=0.2)
        time.sleep(0.5)
        
        click_and_hold(hwnd, *GAME_SHOVEL_POSITION, duration=0.2)
        time.sleep(0.5)
        
        start_time = time.time()  # 记录循环开始时间
        timeout = 10  # 设置超时时间（秒）

        while time.time() - start_time < timeout:  
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            search_area = (left + 400, top + 165, left + 1370, top + 800)
            screenshot = ImageGrab.grab(bbox=search_area)
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            print(screenshot)
            white_pixels = np.where((screenshot[:, :, 0] == 255) & (screenshot[:, :, 1] == 255) & (screenshot[:, :, 2] == 255))

            if len(white_pixels[0]) > 0:
                last_white_pixel = (white_pixels[1][-1], white_pixels[0][-1])
                target_x = search_area[0] + last_white_pixel[0] - 5
                target_y = search_area[1] + last_white_pixel[1] - 5
                click_and_hold(hwnd, target_x, target_y, duration=0.2)
                click_and_hold(hwnd, *GAME_HARVEST_POSITION, duration=0.2)
            else:
                break

def boss_loop():
    """Boss 循环"""
    print("请选择功能：")
    print("1. BOSS 01")
    print("2. BOSS 02")
    choice = input("请输入选项 (1-2): ")

    if choice == '1':
        boss_01_loop()
    elif choice == '2':
        boss_02_loop()

def boss_01_loop():
    """BOSS 01 循环"""
    while running:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        game_area = (left, top, right, bottom)

        screenshot = ImageGrab.grab(bbox=game_area)
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(BOSS_IMAGE, cv2.IMREAD_GRAYSCALE)
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= THRESHOLD:
            center_x = game_area[0] + max_loc[0] + template.shape[1] // 2
            center_y = game_area[1] + max_loc[1] + template.shape[0] // 2

            print(f"发现老板，等待 {BOSS_DELAY} 秒...")
            time.sleep(BOSS_DELAY)

            click_and_hold(hwnd, center_x, center_y, duration=0)
        time.sleep(0.2)

def boss_02_loop():
    """BOSS 02 循环"""
    while running:
        time.sleep(35)
        click_and_hold(hwnd, *BOSS_02_POSITION, duration=0.2)

        found = False
        while not found:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            game_area = (left, top, right, bottom)

            screenshot = ImageGrab.grab(bbox=game_area)
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

            template = cv2.imread(BOSS_02_IMAGE, cv2.IMREAD_GRAYSCALE)
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= THRESHOLD:
                center_x = game_area[0] + max_loc[0] + template.shape[1] // 2
                center_y = game_area[1] + max_loc[1] + template.shape[0] // 2
                found = True

            if not running:
                break
            time.sleep(0.2)

        if found:
            print(f"发现老板，等待 {BOSS_DELAY} 秒...")
            time.sleep(BOSS_DELAY)
            click_and_hold(hwnd, center_x, center_y, duration=0)  # 点击

def open_v1_loop():
    """开箱(不退出背包版)循环"""
    while running:
        click_and_hold(hwnd, *AFK_CANDY_POSITION, duration=0.2)
        time.sleep(0.1)

def owl_loop():
    """猫头鹰循环"""
    while running:
        find_and_interact_image(OWL_01_IMAGE, click_times=1)
        find_and_interact_image(OWL_02_IMAGE, click_times=1)
        find_and_interact_image(OWL_03_IMAGE, click_times=1)
        find_and_interact_image(OWL_04_IMAGE, click_times=1)
        find_and_interact_image(OWL_05_IMAGE, click_times=1)
        find_and_interact_image(OWL_06_IMAGE, click_times=1)
        find_and_interact_image(OWL_07_IMAGE, click_times=1)
        find_and_interact_image(OWL_08_IMAGE, click_times=1)
        find_and_interact_image(OWL_09_IMAGE, click_times=1)

def farming_loop():
    """游戏循环"""
    while running:
        click_and_hold(hwnd, *ITEM_POSITION)
        time.sleep(0.2)

        find_and_interact_image(FARMING_BOOST_IMAGE, duration=0.3)
        time.sleep(0.2)

        press_key('ESC')
        time.sleep(2)

        click_and_hold(hwnd, *FARM_POSITION)
        time.sleep(0.5)
        
        find_and_interact_image(FARMING_COLLECTALL_IMAGE)
        time.sleep(0.2)

def copy_item_loop():
    """复制物品循环"""
    copy_count = 0
    while running:
        if keyboard.is_pressed('f1'): 
            while copy_count < 25:
                click_and_hold(hwnd, *COPY_FIRST_STORAGE_POSITION, duration=0.1, click_times=2)
                time.sleep(0.1)

                click_and_hold(hwnd, *COPY_OK_POSITION, duration=0.1)
                time.sleep(0.3)
                
                win32gui.SetForegroundWindow(lua)
                time.sleep(0.2)
                x, y = COPY_EXECUTE_POSITION
                pyautogui.click(x=x, y=y)
                time.sleep(0.3)

                click_and_hold(hwnd, *COPY_FIRST_BAG_POSITION, duration=0.1, click_times=2)
                time.sleep(0.1)
                
                copy_count += 1
            copy_count = 0
            
        time.sleep(0.1)  

def paying_loop():
    """洞穴祈祷循环"""
    fight_count = 0
    try:
        choice = input("请输入战斗次数: ")
        num_fights = int(choice)  
    except ValueError:
        print("请输入数字")
        return
        
    while running:
        click_and_hold(hwnd, *ITEM_POSITION)
        time.sleep(0.2)
        
        find_and_interact_image(HOLE_BOOST_IMAGE, duration=0.3, click_times=15, delay=0.2)
        
        press_key('ESC')
        time.sleep(0.2)
        
        click_and_hold(hwnd, *PAYING_HEAD_POSITION, duration=0.1)
        time.sleep(0.2)
        
        click_and_hold(hwnd, *PAYING_STORY_POSITION, duration=0.1)
        time.sleep(0.2)
        
        while fight_count < num_fights:
            click_and_hold(hwnd, *PAYING_FIGHT_POSITION, duration=0.1)
            time.sleep(2.5)
            
            click_and_hold(hwnd, *PAYING_SWORD_1_POSITION, duration=0.1)
            time.sleep(0.1)
            click_and_hold(hwnd, *PAYING_SWORD_2_POSITION, duration=0.1)
            time.sleep(0.1)
            click_and_hold(hwnd, *PAYING_SWORD_3_POSITION, duration=0.1)
            time.sleep(0.1)
            click_and_hold(hwnd, *PAYING_SWORD_4_POSITION, duration=0.1)
            time.sleep(0.1)
            click_and_hold(hwnd, *PAYING_SWORD_5_POSITION, duration=0.1)
            time.sleep(5.6)
            
            click_and_hold(hwnd, *PAYING_TREASURE_1_POSITION, duration=0.1)
            time.sleep(3)
            
            fight_count += 1
        fight_count = 0
        click_and_hold(hwnd, *PAYING_RUN_POSITION, duration=0.1)
        time.sleep(5)  

# --- 测试用函数 ---	

def test_loop():
    """测试循环"""



def main():
    """主函数"""
    global running

    exit_thread = threading.Thread(target=exit_handler)
    exit_thread.daemon = True
    exit_thread.start()

    print("请选择功能：")
    print("0. 测试")
    print("1. AFK 刷怪")
    print("2. AFK 合成")
    print("3. 航海")
    print("4. 邮差")
    print("5. 地牢骰子")
    print("6. 养殖")
    print("7. 游戏")
    print("8. Boss")
    print("9. 开箱")
    print("10. 猫头鹰")
    print("11. 农场")
    print("12. 复制物品")
    print("13. 洞穴祈祷")
    choice = input("请输入选项 (1-13): ")

    print("脚本运行中，按下 'delete' 键退出...")
    functions = {
        "0": test_loop,
        "1": lambda: afk_loop(config),
        "2": afk_splice_loop,
        "3": sailing_loop,
        "4": postman_loop,
        "5": dungeon_lootroll_loop,
        "6": breeding_loop,
        "7": gaming_loop,
        "8": boss_loop,
        "9": open_v1_loop,
        "10": owl_loop,
        "11": farming_loop,
        "12": copy_item_loop,
        "13": paying_loop
    }
    
    selected_function = functions.get(choice)
    if selected_function:
        selected_function()
    else:
        print("无效选项！")

if __name__ == "__main__":
    main()