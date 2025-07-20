from playwright.sync_api import sync_playwright

# 用于存储捕获到的请求头信息
all_request_headers_info = []


def handle_request(request):
    """
    捕获每个请求的URL, 方法和头部信息
    """
    # print(f"Intercepted request to: {request.url}") # 调试时可以取消注释
    all_request_headers_info.append({
        "url": request.url,
        "method": request.method,
        "headers": request.headers  # request.headers 是一个字典
    })


def main():
    with sync_playwright() as p:
        # 启动浏览器，可以是 chromium, firefox, or webkit
        # headless=False 可以看到浏览器操作，True则为无头模式
        browser = p.chromium.launch(headless=True,
                                    args=[
                                        '--no-sandbox',
                                        '--disable-setuid-sandbox',
                                        '--disable-dev-shm-usage'  # 有时也需要这个，但 --shm-size 更好
                                    ])

        # 创建一个新的浏览器上下文
        # 可以在这里设置 user_agent, viewport, etc.
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
        )

        # 在上下文中创建一个新页面
        page = context.new_page()

        # 注册请求拦截器，这必须在导航之前完成
        # 'request' 事件会在每个HTTP请求发起时触发
        page.on("request", handle_request)

        print(f"Navigating to https://grok.com/ ...")
        try:
            # 访问目标网站，设置一个合理的超时时间（例如60秒）
            page.goto("https://grok.com/", timeout=60000)
            page.wait_for_timeout(5000)
            print("Page loaded. Waiting for 10 seconds for dynamic content or further requests...")

            # 检查是否仍然被 Cloudflare 阻止 (例如，查找特定的标题或元素)
            title = page.title()
            print(f"Page title: {title}")

            if "请稍候…" in page.content() or "Just a moment..." in page.content() or "Cloudflare" in title or "Checking your browser" in title:
                print("Still on a Cloudflare challenge page. Waiting longer or trying interaction...")
                # 你可能需要在这里添加更长的等待或模拟用户交互
                # 例如，等待特定的元素出现，表明挑战已通过
                try:
                    page.wait_for_selector("body:not(:has-text('请稍候…'))", timeout=60000)
                    print("Cloudflare challenge likely passed.")
                    title = page.title()
                    print(f"New page title: {title}")
                    page.screenshot(path="cf_passed.png")
                except Exception as e:
                    print(f"Failed to pass Cloudflare challenge after extended wait: {e}")
                    page.screenshot(path="cf_failed.png")
            else:
                print("Successfully navigated to the page.")
                page.screenshot(path="cf_success.png")

            page.evaluate("""
                function(){
                    const element = document.getElementById('turnstile-widget');
                    if (element) {
                      element.style.display = 'none';
                    }
                }
            """)
            page.wait_for_timeout(10000)

            try:
                textarea_locator = page.get_by_label("Ask Grok anything")
                textarea_locator.fill("你好")
                print("Successfully entered '你好' into the textarea.")
            except Exception as e:
                print(f"Could not find or fill the textarea with aria-label 'Ask Grok anything'. Error: {e}")
                browser.close()
                return

                # 2. 查找 aria-label 为“提交”的 button 并点击
                # 使用 get_by_role('button', name='...') 是 Playwright 推荐的方式来查找具有特定可访问名称的按钮
            try:
                submit_button_locator = page.get_by_role("button", name="Submit")
                submit_button_locator.click()
                print("Successfully clicked the 'Submit' button.")
            except Exception as e:
                print(f"Could not find or click the button with aria-label 'Submit'. Error: {e}")
                browser.close()
                return

            # 等待10秒
            # Playwright 的 page.wait_for_timeout() 是首选，因为它与Playwright的事件循环集成
            # page.wait_for_timeout(10000)
            # 或者使用 time.sleep(10) 也可以，但在Playwright脚本中前者更佳

            print("\n--- Cookies ---")
            # 获取当前上下文中的所有cookies
            cookies = context.cookies()
            if cookies:
                for cookie in cookies:
                    print(
                        f"Name: {cookie['name']}, Value: {cookie['value']}, Domain: {cookie['domain']}, Path: {cookie['path']}")
            else:
                print("No cookies found.")

            print("\n--- Request Headers (collected during the session) ---")
            if all_request_headers_info:
                # 打印捕获到的每个请求的头部信息
                # 注意：这里会包含所有资源的请求（HTML, CSS, JS, XHR, 图片等）
                for i, req_info in enumerate(all_request_headers_info):
                    if req_info['url'] == 'https://grok.com/rest/app-chat/conversations/new':
                        datas = {
                            'x-xai-request-id': req_info['headers']['x-xai-request-id'],
                            'x-statsig-id': req_info['headers']['x-statsig-id'],
                            'user-agent': req_info['headers']['user-agent'],
                        }
                        print(datas)
                        return datas
            else:
                print("No requests were intercepted (this is unlikely if the page loaded).")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # 确保浏览器关闭
            print("\nClosing browser...")
            page.close()
            browser.close()
        return None


if __name__ == "__main__":
    main()