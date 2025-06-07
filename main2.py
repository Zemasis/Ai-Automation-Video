import os
import sys
from playwright.sync_api import BrowserContext, Page # Không cần sync_playwright ở đây nữa
import pyperclip

# --- CẤU HÌNH ĐĂNG NHẬP (THAY ĐỔI THÔNG TIN NÀY) ---
# LƯU Ý: Nếu đây là tài khoản thật, hãy cân nhắc sử dụng biến môi trường hoặc file cấu hình riêng
# để bảo mật thông tin đăng nhập, thay vì hardcode trực tiếp vào code.
YOUR_RUNWAY_EMAIL = "TanTai911" 
YOUR_RUNWAY_PASSWORD = "Lmhtkaiserx9110" 

# Đảm bảo USER_DATA_DIR này giống hệt trong main.py
USER_DATA_DIR = "playwright_user_data_shared" # Thư mục dùng chung cho cả main.py và main2.py

# Đường dẫn ảnh không cần thiết cho bước đăng nhập, nhưng giữ lại nếu bạn sẽ thêm phần tạo video sau
# INPUT_IMAGE_PATH = "C:\\Users\\your_user\\Desktop\\your_image.jpg" 

# ---------------------------------------------------------------------

# --- Biến global để quản lý Playwright instance và BrowserContext dùng chung ---
# Các biến này sẽ được hàm get_playwright_context() khởi tạo và quản lý
# (Bạn đã có hàm get_playwright_context() trong main.py và nó được main.py gọi)
# (main2.py sẽ nhận browser_context trực tiếp qua tham số hàm)

def login_and_generate_runway_video(video_prompt: str, browser_context: BrowserContext):
    page = browser_context.new_page()
    
    print("[main2.py] Đang điều hướng đến RunwayML để đăng nhập...")
    page.goto("https://app.runwayml.com/auth/login", wait_until="load",timeout=60000)
    page.wait_for_timeout(3000)  # Đợi thêm

    # Kiểm tra đã đăng nhập chưa
    if "/workspace" in page.url:
        print("[main2.py] Đã đăng nhập sẵn rồi.")
        return

    try:
        # Điền email
        email_input = page.locator('input[name="usernameOrEmail"]')
        email_input.wait_for(state="visible", timeout=30000)
        email_input.fill(YOUR_RUNWAY_EMAIL)
        
        # Điền password
        password_input = page.locator('input[name="password"]')
        password_input.fill(YOUR_RUNWAY_PASSWORD)
        
        # Click nút đăng nhập (dùng class hoặc XPath)
        login_button = page.locator('button.Button-jIzJvZ')  # Hoặc 'button[type="submit"]'
        login_button.wait_for(state="visible", timeout=30000)
        assert login_button.is_enabled(), "Nút đăng nhập bị disabled!"
        login_button.scroll_into_view_if_needed()
        login_button.click()

        # Chờ chuyển trang
        page.wait_for_load_state("load", timeout=60000)  # Chờ trang mới load xong
        print("[main2.py] Trang đã chuyển sau khi đăng nhập:", page.url)

        
    except Exception as e:
        print(f"[main2.py] Lỗi đăng nhập: {str(e)}")
        page.screenshot(path="login_error.png")  # Lưu ảnh lỗi
        raise
    


    # Tìm prompt box
    prompt_box = page.locator('div[aria-label="Text Prompt Input"][contenteditable="true"][data-lexical-editor="true"]')
    prompt_box.wait_for(state="visible", timeout=10000)

    # Focus
    prompt_box.evaluate("(el) => el.focus()")
    prompt_box.evaluate('(el) => console.log("DEBUG prompt box: ", el)')
    prompt_box.evaluate('(el) => console.log("Has __lexicalEditor:", !!el.__lexicalEditor)')


    # Copy text vào clipboard bằng Python (cần thư viện pyperclip)
    pyperclip.copy(video_prompt)

    # Bấm Ctrl + A rồi Ctrl + V
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(video_prompt, delay=20) 
    page.wait_for_timeout(1000)  # Chờ nội dung dán xong

    # Kiểm tra nội dung đã đúng chưa
    current_text = prompt_box.inner_text()
    if video_prompt.lower() not in current_text.lower():
        raise Exception(f"❌ Prompt không khớp: '{current_text}'")
    
    print("✅ Prompt đã được dán thành công.")