import main2
import shlex
from playwright.sync_api import sync_playwright, BrowserContext, Page # Import BrowserContext và Page

# --- CẤU HÌNH CHUNG ---
# Thư mục để lưu trữ dữ liệu phiên của Playwright (cookies, local storage, v.v.)
# Đảm bảo các script khác cũng dùng chung thư mục này nếu bạn muốn chia sẻ phiên đăng nhập.
USER_DATA_DIR = "playwright_user_data_shared" 
# ---------------------

# --- Khởi tạo Playwright ở cấp độ module ---
# Đối tượng 'p' sẽ được khởi tạo một lần khi script bắt đầu chạy.
# Nó sẽ không tự động đóng cho đến khi chương trình Python kết thúc hoặc p.stop() được gọi tường minh.
# Chúng ta sẽ không dùng 'with sync_playwright() as p:' trong các hàm nữa.
_playwright_instance = None
_browser_context = None

def get_playwright_context():
    """
    Trả về hoặc khởi tạo đối tượng Playwright và BrowserContext dùng chung.
    """
    global _playwright_instance, _browser_context
    if _playwright_instance is None:
        _playwright_instance = sync_playwright().start()
        print("Đã khởi tạo Playwright instance.")
    
    if _browser_context is None:
        _browser_context = _playwright_instance.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False # Rất quan trọng để quan sát
        )
        print(f"Đã khởi tạo BrowserContext tại thư mục: {USER_DATA_DIR}")
        
    return _browser_context

def get_prompt_from_gemini(query_prompt: str) -> str:
    """
    Truy cập Gemini, nhập prompt và lấy kết quả trả về.
    Sẽ mở một tab mới và không đóng trình duyệt.
    Args:
        query_prompt (str): Câu hỏi hoặc yêu cầu gửi đến Gemini.
    Returns:
        str: Nội dung trả lời từ Gemini. Trả về chuỗi rỗng nếu có lỗi.
    """
    browser_context = get_playwright_context()
    page = browser_context.new_page() # Mở một tab mới cho Gemini

    try:
        print("Đang điều hướng đến Gemini...")
        page.goto("https://gemini.google.com/")

        prompt_input_locator = page.get_by_role("textbox", name="Enter a prompt here")

        print("Đang chờ trường nhập liệu Gemini xuất hiện...")
        try:
            prompt_input_locator.wait_for(state='visible', timeout=45000)
            print("Đã tìm thấy trường nhập liệu Gemini.")
        except Exception as e:
            print(f"Lỗi: Không tìm thấy trường nhập liệu Gemini sau khi chờ. Lỗi: {e}")
            page.close() # Đóng tab Gemini nếu có lỗi
            return ""

        print(f"Đang nhập prompt: \"{query_prompt}\"")
        prompt_input_locator.fill(query_prompt)
        print("Đã nhập prompt. Đang nhấn Enter...")
        page.keyboard.press("Enter")

        print("Đang chờ kết quả từ Gemini xuất hiện...")
        gemini_response_selector = 'message-content.model-response-text' 
        try:
            page.wait_for_selector(gemini_response_selector, state='visible', timeout=90000)
            page.wait_for_timeout(2000) # Đợi thêm để đảm bảo nội dung đã tải
            
            result_element = page.locator(gemini_response_selector)
            gemini_output = result_element.inner_text()

            print("\n--- KẾT QUẢ TỪ GEMINI ---")
            print(gemini_output)
            print("-------------------------\n")
            
            # Không đóng page.close() ở đây, để tab vẫn mở cho người dùng xem
            # Nếu bạn muốn đóng tab Gemini sau khi lấy kết quả, hãy thêm:
            # page.close()
            
            return gemini_output

        except Exception as e:
            print(f"Lỗi: Không lấy được kết quả từ Gemini hoặc selector không đúng: {e}")
            page.close()
            return ""
    except Exception as overall_e:
        print(f"Lỗi tổng thể trong get_prompt_from_gemini: {overall_e}")
        # Không đóng browser_context ở đây, chỉ đóng page nếu có.
        # page.close() # Nếu bạn muốn đóng page nếu có lỗi tổng thể
        return ""

# --- QUY TRÌNH CHÍNH CỦA BẠN ---
if __name__ == "__main__":
    # Đảm bảo context được khởi tạo trước khi gọi bất kỳ hàm nào khác
    main_browser_context = get_playwright_context() # Khởi tạo hoặc lấy context dùng chung

    gemini_query = "Create prompt about Cinematic transition from a parking lot to a neon-lit city at night (just text, no code, no markdown, no comments)"
    generated_video_prompt = get_prompt_from_gemini(gemini_query)

    if generated_video_prompt:
        print("Đã lấy được prompt tạo video từ Gemini.")
        print("Trình duyệt vẫn mở. Bạn có thể kiểm tra tab Gemini.")
        
        # --- GỌI main2.py VÀ TRUYỀN PROMPT ---
        print("\n[main.py] Đang gọi main2.py để xử lý RunwayML...")
        # Lệnh này sẽ chạy main2.py trong một tiến trình Python riêng
        # và truyền generated_video_prompt như một tham số dòng lệnh.
        main2.login_and_generate_runway_video(generated_video_prompt, main_browser_context)

        
        print("[main.py] main2.py đã hoàn tất hoặc đang chạy. Quay lại main.py.")

    else:
        print("Không lấy được prompt từ Gemini.")
    print("\nScript đã hoàn thành bước Gemini. Trình duyệt vẫn mở.")
    print("Vui lòng đóng cửa sổ trình duyệt thủ công khi bạn hoàn tất, hoặc chạy script tiếp theo.")
    input("Nhấn Enter để kết thúc chương trình Python (trình duyệt sẽ vẫn mở cho đến khi bạn đóng thủ công).")
    # Ở đây chúng ta không gọi browser_context.close() hay p.stop()
    # để trình duyệt vẫn mở sau khi script Python này kết thúc.
    # Tuy nhiên, nếu bạn muốn đóng nó khi script này kết thúc, hãy thêm:
    # if _browser_context: _browser_context.close()
    # if _playwright_instance: _playwright_instance.stop()