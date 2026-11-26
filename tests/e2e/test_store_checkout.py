"""Browser regression tests for the public product page and checkout routing."""
import os
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        home_response = page.goto(BASE_URL + "/")
        assert home_response and home_response.status == 200, "Home page did not load"
        expect(page.get_by_text("Currently in Testing")).to_be_visible()
        page.get_by_text("Share feedback").click()
        expect(page.locator("#feedback-message")).to_be_visible()
        expect(page.locator("#feedback-category")).to_be_visible()

        response = page.goto(f"{BASE_URL}/products/selected_product/98765/")
        assert response and response.status == 200, "Product detail page did not load"

        quantity = page.locator("#qty")
        expect(quantity).to_have_value("1")

        page.locator("#qty-increase").click()
        expect(quantity).to_have_value("1.250")

        page.locator("#qty-decrease").click()
        expect(quantity).to_have_value("1.000")

        quantity.fill("0.250")
        page.locator("#qty-decrease").click()
        expect(quantity).to_have_value("0.250")

        quantity.fill("100")
        page.locator("#qty-increase").click()
        expect(quantity).to_have_value("100.000")

        quantity.fill("1.500")
        page.get_by_role("button", name="Buy Now").click()
        page.wait_for_url("**/login/**", timeout=10000) if "/login/" in page.url else page.wait_for_timeout(500)
        assert "/products/Checkout/98765/1.500/" in page.url or "next=" in page.url, (
            f"Buy Now did not preserve selected product/quantity: {page.url}"
        )

        assert not errors, "Browser JavaScript errors: " + "; ".join(errors)
        browser.close()


if __name__ == "__main__":
    main()
