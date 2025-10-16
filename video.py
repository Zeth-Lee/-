from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 配置Edge浏览器
edge_options = Options()
# 如果不想看到浏览器界面，可以取消下面这行的注释
# edge_options.add_argument('--headless')
edge_options.add_argument('--disable-blink-features=AutomationControlled')
edge_options.add_experimental_option('excludeSwitches', ['enable-automation'])
edge_options.add_experimental_option('useAutomationExtension', False)

# 视频ID范围
start_video_id = 69647501
end_video_id = 69647635
base_url = "https://buaa.yuketang.cn/pro/lms/CTRhhgJSDtg/28447694/video/"

def check_completion(driver):
    """检查视频完成度是否为100%"""
    try:
        # 查找完成度元素
        completion_element = driver.find_element(By.XPATH, 
            "//span[@class='text' and contains(text(), '完成度：')]")
        completion_text = completion_element.text
        print(f"当前完成度: {completion_text}")
        
        # 判断是否为100%
        if "100%" in completion_text:
            return True
        return False
    except Exception as e:
        print(f"检查完成度时出错: {e}")
        return False

def is_video_content(driver):
    """判断当前页面是否为可播放的视频内容"""
    try:
        # 检查是否存在播放按钮
        play_button = driver.find_elements(By.CSS_SELECTOR, "xt-playbutton.xt_video_player_play_btn")
        if play_button:
            print("检测到视频播放按钮，这是视频内容")
            return True
        
        # 检查是否存在视频播放器
        video_player = driver.find_elements(By.CSS_SELECTOR, "video, .xt_video_player")
        if video_player:
            print("检测到视频播放器，这是视频内容")
            return True
        
        # 检查是否为习题页面
        exercise = driver.find_elements(By.CSS_SELECTOR, ".exercise, .problem, .question")
        if exercise:
            print("检测到习题内容，跳过")
            return False
        
        # 检查页面是否加载失败
        error_messages = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '加载失败') or contains(text(), '无法加载') or contains(text(), '404') or contains(text(), '错误')]")
        if error_messages:
            print("页面加载失败，跳过")
            return False
        
        print("无法确定内容类型，尝试作为视频处理")
        return True
        
    except Exception as e:
        print(f"判断内容类型时出错: {e}")
        return False

def is_video_playing(driver):
    """检查视频是否正在播放"""
    try:
        # 检查是否存在暂停按钮（如果视频在播放，按钮应该显示暂停）
        pause_button = driver.find_elements(By.CSS_SELECTOR, "xt-playbutton.xt_video_player_play_btn[class*='pause']")
        if pause_button:
            return True
        
        # 通过JavaScript检查视频元素的播放状态
        video_elements = driver.find_elements(By.TAG_NAME, "video")
        if video_elements:
            is_playing = driver.execute_script(
                "return arguments[0].paused === false && arguments[0].ended === false;", 
                video_elements[0]
            )
            return is_playing
        
        return False
    except:
        return False

def click_play_button(driver):
    """点击播放按钮"""
    try:
        play_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "xt-playbutton.xt_video_player_play_btn"))
        )
        play_button.click()
        print("已点击播放按钮")
        return True
    except Exception as e:
        print(f"点击播放按钮失败: {e}")
        try:
            play_button = driver.find_element(By.CSS_SELECTOR, "xt-playbutton")
            play_button.click()
            print("使用备用方法点击播放按钮")
            return True
        except:
            print("无法找到或点击播放按钮")
            return False

def play_video(driver, video_id):
    """播放指定ID的视频"""
    url = f"{base_url}{video_id}"
    print(f"\n正在打开视频: {url}")
    driver.get(url)
    
    # 等待页面加载
    time.sleep(5)
    
    # 判断是否为可播放的视频内容
    if not is_video_content(driver):
        print(f"视频 {video_id} 不是可播放内容，跳过")
        return False
    
    # 点击播放按钮
    if not click_play_button(driver):
        print(f"视频 {video_id} 无法播放，跳过")
        return False
    
    time.sleep(2)  # 等待视频开始播放
    
    # 监控视频完成度
    check_interval = 10  # 每10秒检查一次
    last_check_time = time.time()
    pause_check_count = 0  # 连续检测到暂停的次数
    
    while True:
        time.sleep(check_interval)
        
        # 检查视频是否被暂停
        if not is_video_playing(driver):
            pause_check_count += 1
            print(f"检测到视频可能已暂停 (第{pause_check_count}次)")
            
            # 连续2次检测到暂停，尝试重新播放
            if pause_check_count >= 2:
                print("尝试重新点击播放按钮...")
                if click_play_button(driver):
                    pause_check_count = 0  # 重置计数
                    time.sleep(2)
                else:
                    print("无法恢复播放，可能视频已结束")
        else:
            pause_check_count = 0  # 视频正在播放，重置计数
        
        # 检查完成度
        if check_completion(driver):
            print(f"视频 {video_id} 已完成！")
            return True
        else:
            current_time = time.time()
            elapsed = int(current_time - last_check_time)
            print(f"视频播放中... (已监控 {elapsed} 秒)")
            last_check_time = current_time

def main():
    # 初始化Edge浏览器
    driver = webdriver.Edge(options=edge_options)
    driver.maximize_window()
    
    try:
        print("开始自动播放视频序列...")
        print(f"视频ID范围: {start_video_id} 到 {end_video_id}")
        
        # 从起始视频ID到结束视频ID依次播放
        completed_count = 0
        skipped_count = 0
        
        for video_id in range(start_video_id, end_video_id + 1):
            print(f"\n{'='*50}")
            print(f"正在处理视频 {video_id}")
            print(f"进度: {video_id - start_video_id + 1}/{end_video_id - start_video_id + 1}")
            print(f"已完成: {completed_count} | 已跳过: {skipped_count}")
            print(f"{'='*50}")
            
            result = play_video(driver, video_id)
            
            if result:
                completed_count += 1
            else:
                skipped_count += 1
            
            # 等待一小段时间再进入下一个视频
            time.sleep(3)
        
        print("\n" + "="*50)
        print("所有视频处理完成！")
        print(f"成功完成: {completed_count} 个")
        print(f"跳过: {skipped_count} 个")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n用户中断了程序")
    except Exception as e:
        print(f"\n程序出错: {e}")
    finally:
        print("\n5秒后关闭浏览器...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    # 提示用户
    print("=" * 60)
    print("视频自动播放脚本")
    print("=" * 60)
    print("\n注意事项:")
    print("1. 请确保已安装Edge浏览器")
    print("2. 请确保已安装selenium库: pip install selenium")
    print("3. 脚本会自动下载对应的Edge驱动")
    print("4. 如果需要登录，请在第一个视频页面手动登录")
    print("5. 按Ctrl+C可以随时中断程序")
    print("\n" + "=" * 60)
    
    input("按Enter键开始运行...")
    main()