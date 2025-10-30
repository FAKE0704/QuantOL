import pyautogui
import time
import os
from datetime import datetime

class ButtonDetector:
    def __init__(self):
        self.buttons = {}
        self.template_dir = r'C:\Users\0704\awesome-Qsys\src\core\execution'
        
    def prepare_window(self):
        """准备同花顺窗口"""
        print("请确保同花顺交易窗口已打开并处于最前")
        time.sleep(5)  # 给用户时间调整窗口
        return True

    def detect_buttons(self):
        """扫描目录下所有.png文件作为按钮模板并识别"""
        try:
            button_list = []
            # 获取目录下所有.png文件
            for filename in os.listdir(self.template_dir):
                if filename.endswith('.png'):
                    name = filename[:-4]  # 去掉.png后缀作为按钮名
                    template_path = os.path.join(self.template_dir, filename)
                    
                    # 识别按钮（只取第一个匹配项）
                    btn = pyautogui.locateOnScreen(template_path, confidence=0.8)
                    if btn:
                        btn_info = {
                            'name': name,
                            'position': (btn.left, btn.top, btn.width, btn.height),
                            'last_clicked': None,
                            'click_count': 0,
                            'template': filename
                        }
                        self.buttons[name] = btn_info
                        button_list.append(btn_info)
                        print(f"识别到按钮: {name} 位置: {btn_info['position']}")
            
            return button_list
        except Exception as e:
            print(f"按钮识别失败: {e}")
            return []

    def click_button(self, button_ref):
        """点击指定按钮，支持按钮名或按钮对象，调用方式click_button(detector.buttons['buy'])"""
        try:
            if isinstance(button_ref, str):  # 通过按钮名点击
                if button_ref not in self.buttons:
                    print(f"未找到按钮: {button_ref}")
                    return False
                button_info = self.buttons[button_ref]
            else:  # 直接使用按钮对象
                button_info = button_ref
                
            x, y = button_info['position'][0] + 10, button_info['position'][1] + 10
            
            # 显示鼠标移动过程
            current_x, current_y = pyautogui.position()
            pyautogui.moveTo(current_x, current_y, duration=0.1)  # 短暂停留当前位置
            pyautogui.moveTo(x, y, duration=0.7)  # 平滑移动到目标位置
            time.sleep(0.2)  # 点击前暂停
            
            # 模拟点击并记录行为
            pyautogui.click()
            button_info['last_clicked'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            button_info['click_count'] += 1
            print(f"已点击按钮: {button_info['name']}")
            return True
        except Exception as e:
            print(f"点击按钮失败: {e}")
            return False

if __name__ == "__main__":
    detector = ButtonDetector()
    if detector.prepare_window():
        print("正在识别按钮...")
        buttons = detector.detect_buttons()
        
        # 示例用法
        print("识别到的按钮:", list(detector.buttons.keys()))
        # 通过名称点击buy按钮
        if 'simbuy' in detector.buttons:
            detector.click_button(detector.buttons['simbuy'])
        
        detector.detect_buttons()
        if 'simbuyensure' in detector.buttons:
            detector.click_button(detector.buttons['simbuyensure'])
