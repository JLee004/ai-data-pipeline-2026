import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

try:
    # 1. 웹페이지 열기
    driver.get('https://quotes.toscrape.com/')

    # 페이지가 로드될 때까지 대기
    wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, 'footer'))
    )

    # 2. Login 클릭
    login_link = wait.until(
        EC.element_to_be_clickable((By.LINK_TEXT, 'Login'))
    )
    login_link.click()

    # 3. 로그인 정보 입력
    username_input = wait.until(
        EC.presence_of_element_located((By.ID, 'username'))
    )

    password_input = driver.find_element(By.ID, 'password')

    username_input.send_keys('admin')
    password_input.send_keys('admin')

    # 4. 로그인 버튼 클릭
    login_btn = driver.find_element(
        By.CSS_SELECTOR,
        'input[type="submit"]'
    )
    login_btn.click()

    # 5. 로그인 완료 확인
    wait.until(
        EC.presence_of_element_located((By.LINK_TEXT, 'Logout'))
    )

    print('로그인 성공')


    # 6. 데이터를 저장할 리스트
    rows = []


    # 7. 최대 10페이지 반복
    for page_num in range(1, 11):

        # 페이지가 로드될 때까지 대기
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'footer'))
        )

        print(f'{page_num} 페이지 수집')

        # 현재 페이지의 모든 quote 가져오기
        quotes = driver.find_elements(
            By.CSS_SELECTOR,
            '.quote'
        )


        # 한 페이지의 quote들을 하나씩 반복
        for quote in quotes:

            # 명언
            text = quote.find_element(
                By.CSS_SELECTOR,
                '.text'
            ).text

            # 작가
            author = quote.find_element(
                By.CSS_SELECTOR,
                '.author'
            ).text

            # 작가 상세 페이지 링크
            link = quote.find_element(
                By.CSS_SELECTOR,
                'span > a'
            ).get_attribute('href')

            # 태그
            tags = quote.find_elements(
                By.CSS_SELECTOR,
                '.tags > a'
            )

            tag_text = ', '.join(
                tag.text for tag in tags
            )


            # 한 개의 quote 정보를 dictionary로 저장
            rows.append({
                'text': text,
                'author': author,
                'link': link,
                'tags': tag_text
            })


        # 8. Next 버튼 찾기
        # find_elements()를 사용하면
        # 없을 경우 에러 대신 []를 반환
        next_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            'li.next a'
        )

        # Next가 없으면 마지막 페이지
        if not next_buttons:
            print('마지막 페이지입니다.')
            break

        # 다음 페이지 이동
        next_buttons[0].click()


    # 9. DataFrame 만들기
    df_quotes = pd.DataFrame(rows)


    # 10. 중복 제거
    df_quotes = df_quotes.drop_duplicates(
        subset=['text', 'author']
    )


    # 11. CSV 저장
    df_quotes.to_csv(
        'quotes_100.csv',
        index=False,
        encoding='utf-8-sig'
    )

    print(f'파일 저장 완료: {len(df_quotes)}건')


    # 12. 로그아웃
    logout_link = driver.find_element(
        By.LINK_TEXT,
        'Logout'
    )

    logout_link.click()

    print('로그아웃 완료')


# 실제 오류 내용을 e에 저장
except Exception as e:
    print('실행 중 오류 발생:')
    print(e)


# 성공/실패 관계없이 항상 실행
finally:
    driver.quit()
    print('브라우저 종료')

