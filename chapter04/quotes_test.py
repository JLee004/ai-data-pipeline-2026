import keyring
from playwright.sync_api import sync_playwright


# =========================================================
# 1. 저장해둔 다나와 ID / Password 가져오기
# =========================================================

user_id = keyring.get_password('danawa.com', 'user_id')

if user_id is None:
    raise ValueError('저장된 다나와 ID가 없습니다.')

password = keyring.get_password('danawa.com', user_id)

if password is None:
    raise ValueError('저장된 다나와 비밀번호가 없습니다.')


# =========================================================
# 2. Playwright 시작
# =========================================================

with sync_playwright() as p:

    # -----------------------------------------------------
    # 브라우저 실행
    # -----------------------------------------------------

    browser = p.chromium.launch(headless=False)

    # Selenium:
    # driver = webdriver.Chrome()


    # Playwright에서는 browser 안에 page를 만들어야 함
    page = browser.new_page()


    # =====================================================
    # 3. 다나와 접속
    # =====================================================

    page.goto('https://www.danawa.com/')

    # Selenium:
    # driver.get('https://www.danawa.com/')


    # =====================================================
    # 4. 페이지가 로딩되었는지 확인
    # =====================================================

    page.locator('#danawa_footer').wait_for()

    # Selenium:
    # wait.until(
    #     EC.presence_of_element_located(
    #         (By.ID, 'danawa_footer')
    #     )
    # )


    # =====================================================
    # 5. '로그인' 링크 클릭
    # =====================================================

    page.get_by_text('로그인', exact=True).click()

    # Selenium:
    # driver.find_element(
    #     By.LINK_TEXT,
    #     '로그인'
    # ).click()


    # =====================================================
    # 6. ID 입력창 찾기
    # =====================================================

    id_input = page.locator('input[type="text"]')

    # Selenium:
    # id_input = driver.find_element(
    #     By.CSS_SELECTOR,
    #     'input[type="text"]'
    # )


    # =====================================================
    # 7. ID 입력
    # =====================================================

    id_input.fill(user_id)

    # Selenium:
    # id_input.send_keys(user_id)


    # =====================================================
    # 8. Password 입력창 찾기
    # =====================================================

    pass_input = page.locator('input[type="password"]')

    # Selenium:
    # pass_input = driver.find_element(
    #     By.CSS_SELECTOR,
    #     'input[type="password"]'
    # )


    # =====================================================
    # 9. Password 입력
    # =====================================================

    pass_input.fill(password)

    # Selenium:
    # pass_input.send_keys(password)


    # =====================================================
    # 10. 로그인 버튼 찾기
    # =====================================================

    login_btn = page.locator('.btn_login')

    # Selenium:
    # login_btn = driver.find_element(
    #     By.CLASS_NAME,
    #     'btn_login'
    # )


    # =====================================================
    # 11. 로그인 버튼 클릭
    # =====================================================

login_btn.click()

# Selenium:
# login_btn.click()


# 브라우저를 계속 열어두기
input('브라우저를 닫으려면 Enter를 누르세요...')

# browser.close()  ← 일단 주석 처리


    # =====================================================
    # 13. 브라우저 종료
    # =====================================================

   # browser.close()

    # Selenium:
    # driver.quit()