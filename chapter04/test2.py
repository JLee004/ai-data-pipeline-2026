import os
import pandas as pd
from playwright.sync_api import sync_playwright


# CSV 파일 경로
csv_path = os.path.abspath('danawa_products.csv')

print('실행 폴더:', os.getcwd())
print('CSV 저장 위치:', csv_path)


with sync_playwright() as p:

    # 1. 브라우저 실행
    browser = p.chromium.launch(
        headless=False,
        slow_mo=100
    )

    page = browser.new_page()


    # 2. 다나와 상품 페이지 이동
    page.goto(
        'https://prod.danawa.com/list/?cate=11255834&15main_11_02',
        wait_until='domcontentloaded'
    )

    # Selenium:
    # driver.get(
    #     'https://prod.danawa.com/list/?cate=11255834&15main_11_02'
    # )


    # 3. 페이지 로딩 확인
    page.locator('footer').wait_for(state='attached')

    print('페이지 로딩 완료')


    # 4. 한 페이지에 90개 표시
    select = page.locator('select').filter(
        has=page.locator('option[value="90"]')
    ).first

    select.select_option(value='90')

    # Selenium:
    # options = driver.find_elements(By.TAG_NAME, 'option')
    #
    # for option in options:
    #     if option.get_attribute('value') == '90':
    #         option.click()

    print('90개 선택 완료')


    # 5. 동적 페이지 변경 대기
    page.wait_for_timeout(3000)


    # 6. 전체 상품 저장용 list
    all_products = []


    # 7. 1 ~ 10 페이지 반복
    for page_num in range(1, 11):

        print(f'\n===== {page_num} 페이지 =====')


        # 8. 현재 페이지 상품 가져오기
        products = page.locator(
            'div[data-testid="ProductListItem"]'
        )

        # Selenium:
        # products = driver.find_elements(
        #     By.CSS_SELECTOR,
        #     'div[data-testid="ProductListItem"]'
        # )

        product_count = products.count()

        print(
            '현재 페이지 상품 개수:',
            product_count
        )


        # 9. 현재 페이지의 모든 상품 반복
        for i in range(product_count):

            product = products.nth(i)

            # Selenium:
            # product = products[i]

            try:

                # 10. 상품 내부 div
                product_info = product.locator(
                    '.dnw-product-list-item > div'
                )

                # Selenium:
                # product_info = product.find_elements(
                #     By.CSS_SELECTOR,
                #     '.dnw-product-list-item > div'
                # )


                # 11. 제품 정보 영역
                computer_info = product_info.nth(1)

                # Selenium:
                # computer_info = product_info[1]


                # 12. 상품명
                product_name = computer_info.locator(
                    'div a'
                ).first.inner_text()

                # Selenium:
                # product_name = computer_info.find_element(
                #     By.CSS_SELECTOR,
                #     'div a'
                # ).text


                # 13. 컴퓨터 사양
                specs = computer_info.locator(
                    'div[data-testid="ProductListSpecs"]'
                )

                # Selenium:
                # specs = computer_info.find_elements(
                #     By.CSS_SELECTOR,
                #     'div[data-testid="ProductListSpecs"]'
                # )


                # 여러 사양을 하나의 문자열로 합치기
                specs_text = ' '.join(
                    specs.nth(j).inner_text()
                    for j in range(specs.count())
                )

                # Selenium:
                # specs_text = ' '.join(
                #     spec.text for spec in specs
                # )


                # 14. 가격 정보 영역
                price_info = product_info.nth(2)

                # Selenium:
                # price_info = product_info[2]


                # 15. 가격
                price = price_info.locator(
                    'li'
                ).first.inner_text()

                # Selenium:
                # price = price_info.find_element(
                #     By.CSS_SELECTOR,
                #     'li'
                # ).text


                # 16. 상품 정보를 dictionary로 저장
                item = {
                    'page': page_num,
                    'product_name': product_name,
                    'specs': specs_text,
                    'price': price
                }

                all_products.append(item)


                # 진행 상황 출력
                print(
                    f'{i + 1}. '
                    f'{product_name} | '
                    f'{price}'
                )


            except Exception as e:

                print(
                    f'{i + 1}번째 상품 추출 실패:',
                    e
                )


        # ======================================
        # 현재 페이지까지 CSV 저장
        # ======================================

        # 17. list → DataFrame
        df = pd.DataFrame(all_products)


        # 18. 매 페이지마다 CSV 저장
        df.to_csv(
            csv_path,
            index=False,
            encoding='utf-8-sig'
        )

        print('\n------------------------------')
        print(
            f'{page_num}페이지까지 CSV 저장 완료'
        )
        print(
            '현재까지 상품 수:',
            len(df)
        )
        print(
            '저장 위치:',
            csv_path
        )
        print('------------------------------')


        # 19. 10페이지까지 완료했으면 종료
        if page_num == 10:
            break


        # ======================================
        # 다음 페이지 이동
        # ======================================

        try:

            next_page = page.get_by_role(
                'link',
                name=str(page_num + 1),
                exact=True
            ).last

            next_page.click()

            print(
                f'{page_num + 1}페이지로 이동'
            )


            # 동적 페이지 변경 대기
            page.wait_for_timeout(3000)


        except Exception as e:

            print('\n페이지 이동 실패')
            print(e)

            print(
                '\n지금까지 수집한 데이터는 '
                'CSV에 저장되어 있습니다.'
            )

            break


    # ======================================
    # 최종 결과
    # ======================================

    df = pd.DataFrame(all_products)


    print('\n==============================')
    print('Scraping 종료')
    print('전체 수집 상품 수:', len(df))
    print('==============================')


    # 최종 CSV 저장
    df.to_csv(
        csv_path,
        index=False,
        encoding='utf-8-sig'
    )

    print('\nCSV 최종 저장 완료')
    print(csv_path)


    # DataFrame 일부 확인
    print('\n--- 데이터 미리보기 ---')

    print(
        df[
            [
                'page',
                'product_name',
                'specs',
                'price'
            ]
        ].head(10)
    )


    # 브라우저 유지
    input(
        '\n종료하려면 Enter를 누르세요...'
    )