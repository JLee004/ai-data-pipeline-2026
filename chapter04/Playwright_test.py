import os
import re
import pandas as pd
from playwright.sync_api import sync_playwright


# ==========================================
# CSV 저장 위치
# ==========================================

csv_path = os.path.abspath('danawa_900_products.csv')

print('CSV 저장 위치:', csv_path)


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False,
        slow_mo=100
    )

    page = browser.new_page()


    # ==========================================
    # 1. 다나와 접속
    # ==========================================

    page.goto(
        'https://prod.danawa.com/list/?cate=11255834&15main_11_02',
        wait_until='domcontentloaded',
        timeout=60000
    )

    page.wait_for_timeout(5000)

    print('페이지 접속 완료')


    # ==========================================
    # 2. 가능한 상품 selector 확인
    # ==========================================

    selector_candidates = [
        'div[data-testid="ProductListItem"]',
        '.dnw-product-list-item',
        'li.prod_item',
        '.prod_item',
        '.prod_main_info'
    ]


    product_selector = None


    for selector in selector_candidates:

        count = page.locator(selector).count()

        print(
            f'{selector} → {count}개'
        )

        if count > 0 and product_selector is None:
            product_selector = selector


    # ==========================================
    # 상품 selector 못 찾으면 종료
    # ==========================================

    if product_selector is None:

        print('\n상품 selector를 찾지 못했습니다.')

        print(
            '현재 페이지에 상품은 보이지만 '
            'HTML 구조가 기존 코드와 다릅니다.'
        )

        input(
            '\n브라우저를 확인하고 Enter를 누르세요...'
        )

        browser.close()
        raise SystemExit


    print(
        '\n사용할 상품 selector:',
        product_selector
    )


    # ==========================================
    # 3. 90개 보기 설정
    # ==========================================

    select_90 = page.locator(
        'select:has(option[value="90"])'
    ).first


    if select_90.count() > 0:

        select_90.select_option('90')

        print('90개 보기 선택 완료')

        page.wait_for_timeout(5000)

    else:

        print(
            '90개 보기 select를 찾지 못했습니다.'
        )


    # ==========================================
    # 4. 90개 선택 후 selector 다시 확인
    # ==========================================

    # 90개 선택 후 DOM이 바뀔 수 있으므로
    # 다시 selector 확인

    product_selector = None


    for selector in selector_candidates:

        count = page.locator(selector).count()

        print(
            f'90개 선택 후 {selector} → {count}개'
        )

        if count > 0 and product_selector is None:
            product_selector = selector


    if product_selector is None:

        print(
            '\n90개 선택 후 상품 요소를 찾지 못했습니다.'
        )

        input(
            '\n브라우저 확인 후 Enter...'
        )

        browser.close()
        raise SystemExit


    print(
        '\n최종 상품 selector:',
        product_selector
    )


    print(
        '현재 상품 개수:',
        page.locator(product_selector).count()
    )


    # ==========================================
    # 5. 전체 데이터 저장
    # ==========================================

    all_products = []


    # ==========================================
    # 6. 1 ~ 10 페이지 반복
    # ==========================================

    for page_num in range(1, 11):

        print(
            f'\n========== {page_num} 페이지 =========='
        )


        page.wait_for_timeout(2000)


        products = page.locator(
            product_selector
        )


        product_count = products.count()


        print(
            '현재 페이지 상품 수:',
            product_count
        )


        # ======================================
        # 상품 반복
        # ======================================

        for index in range(product_count):

            product = products.nth(index)

            try:

                # ==================================
                # NAME
                # ==================================

                name = ''


                name_candidates = [
                    '.prod_name a',
                    'a[href*="/info/?"][href*="pcode="]',
                    'div a'
                ]


                for selector in name_candidates:

                    locator = product.locator(
                        selector
                    )

                    if locator.count() > 0:

                        text = (
                            locator
                            .first
                            .inner_text()
                            .strip()
                        )

                        if text:
                            name = text
                            break


                # ==================================
                # SPEC
                # ==================================

                spec = ''


                spec_candidates = [
                    '.spec_list',
                    '[data-testid="ProductListSpecs"]',
                    '.prod_spec_set'
                ]


                for selector in spec_candidates:

                    locator = product.locator(
                        selector
                    )

                    if locator.count() > 0:

                        texts = []

                        for i in range(
                            locator.count()
                        ):

                            text = (
                                locator
                                .nth(i)
                                .inner_text()
                                .strip()
                            )

                            if text:
                                texts.append(text)


                        spec = ' / '.join(texts)

                        if spec:
                            break


                # ==================================
                # 전체 상품 text
                # 가격 찾는 fallback용
                # ==================================

                full_text = (
                    product
                    .inner_text()
                    .strip()
                )


                # ==================================
                # PRICE
                # ==================================

                price = ''


                price_match = re.search(
                    r'(\d{1,3}(?:,\d{3})+)\s*원',
                    full_text
                )


                if price_match:

                    price = (
                        price_match.group(1)
                        + '원'
                    )


                # ==================================
                # PRICE SPEC
                # ==================================

                price_spec = ''


                # 예: 32GB, M.2 1TB
                spec_match = re.search(
                    r'(\d+GB[^0-9\n]*M\.2\s*[0-9A-Za-z]+)',
                    full_text
                )


                if spec_match:
                    price_spec = spec_match.group(1)


                # ==================================
                # index
                # ==================================

                global_index = (
                    len(all_products) + 1
                )


                # ==================================
                # 데이터 저장
                # ==================================

                all_products.append({
                    'index': global_index,
                    'computer_name': name,
                    'computer_spec': spec,
                    'price_spec': price_spec,
                    'price': price
                })


                print(
                    f'{global_index:03d}. '
                    f'{name} | '
                    f'{price}'
                )


            except Exception as e:

                print(
                    f'{page_num}페이지 '
                    f'{index + 1}번째 오류:',
                    e
                )


        # ======================================
        # CSV 중간 저장
        # ======================================

        df = pd.DataFrame(
            all_products,
            columns=[
                'index',
                'computer_name',
                'computer_spec',
                'price_spec',
                'price'
            ]
        )


        df.to_csv(
            csv_path,
            index=False,
            encoding='utf-8-sig'
        )


        print(
            '누적 저장 상품:',
            len(df)
        )


        # ======================================
        # 10페이지 종료
        # ======================================

        if page_num == 10:
            break


        # ======================================
        # 다음 페이지 버튼
        # ======================================

        next_page_num = page_num + 1


        next_button = page.get_by_role(
            'link',
            name=str(next_page_num),
            exact=True
        ).last


        if next_button.count() == 0:

            print(
                f'{next_page_num}페이지 버튼 없음'
            )

            break


        # 현재 첫 상품 이름 저장
        old_first_text = ''

        if product_count > 0:

            old_first_text = (
                products
                .first
                .inner_text()
            )


        next_button.click()


        print(
            f'{next_page_num}페이지 클릭'
        )


        # ======================================
        # 상품 목록 실제 변경 기다리기
        # ======================================

        try:

            page.wait_for_function(
                """
                ([selector, oldText]) => {

                    const el =
                        document.querySelector(selector);

                    if (!el) {
                        return false;
                    }

                    return el.innerText !== oldText;
                }
                """,
                arg=[
                    product_selector,
                    old_first_text
                ],
                timeout=20000
            )

        except:

            print(
                '상품 변경 확인 timeout'
            )


        page.wait_for_timeout(3000)


        # ======================================
        # 다음 페이지에서 selector 재확인
        # ======================================

        for selector in selector_candidates:

            if page.locator(selector).count() > 0:

                product_selector = selector
                break


    # ==========================================
    # 최종 저장
    # ==========================================

    df = pd.DataFrame(
        all_products,
        columns=[
            'index',
            'computer_name',
            'computer_spec',
            'price_spec',
            'price'
        ]
    )


    df.to_csv(
        csv_path,
        index=False,
        encoding='utf-8-sig'
    )


    print('\n==============================')
    print('Scraping 완료')
    print('전체 수집 상품:', len(df))
    print('==============================')


    print('\n데이터 미리보기:')
    print(df.head(10))


    print('\nCSV:')
    print(csv_path)


    input(
        '\n종료하려면 Enter를 누르세요...'
    )

    browser.close()