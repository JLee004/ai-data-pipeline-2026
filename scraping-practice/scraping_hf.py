# csv is a built-in Python library for reading and writing CSV tables.
import csv

# re lets us match text patterns, such as text starting with "Published on".
import re

# datetime records when we collected the data.
# timezone lets us use UTC consistently.
from datetime import datetime, timezone

# Path helps us work with file and folder paths.
from pathlib import Path

# urljoin combines a website address with a relative link.
# Example: "/papers/2609.39102" becomes a full Hugging Face URL.
from urllib.parse import urljoin

# sync_playwright lets Python control a browser one step at a time.
from playwright.sync_api import sync_playwright


# This page redirects to the current month's paper listing.
TARGET_URL = "https://huggingface.co/papers/month/2026-10"

# Start with a small sample so we can manually check the results.
PAPER_LIMIT = 3

# __file__ refers to this Python script.
# resolve() finds its absolute path.
# parent selects the folder containing the script.
# / "data" adds a data folder inside that folder.
OUTPUT_FOLDER = Path(__file__).resolve().parent / "data"


def open_page(page, url):
    """Open a webpage and check its HTTP response."""

    # goto() tells the browser tab to visit the URL.
    # domcontentloaded waits until the initial HTML has been parsed.
    # timeout is measured in milliseconds: 30000 means 30 seconds.
    response = page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    # A successful request should return a response with HTTP status 200.
    # If it does not, stop instead of scraping an error page.
    if response is None or response.status != 200:
        # Use the real status when available.
        status = response.status if response else "no response"

        # raise stops normal execution and explains the problem.
        raise RuntimeError(f"Cannot load {url}: HTTP {status}")


def read_count(locator):
    """Read an exact whole-number count from a page element."""

    # inner_text() reads the element's displayed text.
    # strip() removes spaces and line breaks around it.
    # replace() removes commas, changing "1,234" to "1234".
    text = locator.inner_text().strip().replace(",", "")

    # isdigit() checks whether the text contains only numeric digits.
    # We reject unexpected formats instead of guessing a number.
    if not text.isdigit():
        raise ValueError(
            f"Expected an exact number, received: {text!r}"
        )

    # int() converts text such as "671" into the number 671.
    return int(text)


def collect_papers():
    """Collect paper information from the listing and detail pages."""

    # A list will hold all our rows.
    # Each row will be a dictionary.
    records = []

    # Start Playwright.
    # The with statement also handles Playwright cleanup afterward.
    with sync_playwright() as playwright:

        # Launch Chromium.
        # headless=False makes the browser visible while we practice.
        browser = playwright.chromium.launch(headless=False)

        try:
            # Keep the listing open in one tab.
            listing_page = browser.new_page()

            # Use a second tab to visit individual paper pages.
            detail_page = browser.new_page()

            # Set the maximum waiting time for locator operations.
            listing_page.set_default_timeout(30000)
            detail_page.set_default_timeout(30000)

            # Call our helper function to open the monthly listing.
            open_page(listing_page, TARGET_URL)

            # CSS selector explanation:
            # article = a paper card.
            # h3 = the title heading inside the card.
            # a = the link inside that heading.
            #
            # .first selects the first matching link.
            # wait_for() waits until it is visible.
            listing_page.locator("article h3 a").first.wait_for(
                state="visible"
            )

            # Select article elements containing an h3 paper link.
            # filter(has=...) excludes articles without that structure.
            cards = listing_page.locator("article").filter(
                has=listing_page.locator("h3 a")
            )

            # count() tells us how many matching cards are currently loaded.
            # This is not necessarily the total number for the whole month.
            available = cards.count()

            # min() selects the smaller number.
            # For example, if only two cards exist, collect two rather than three.
            amount = min(PAPER_LIMIT, available)

            # f-strings insert variable values inside the printed message.
            print(f"Loaded cards: {available}")
            print(f"Collecting: {amount}")

            # range(amount) produces positions starting at zero.
            # For three papers, index will be 0, 1, and 2.
            for index in range(amount):

                # nth(index) selects the card at that position.
                card = cards.nth(index)

                # Search within this specific card for its title link.
                title_link = card.locator("h3 a")

                # Read the title and remove surrounding whitespace.
                title = title_link.inner_text().strip()

                # Read the link's href attribute.
                # It usually contains a relative path such as /papers/2609.39102.
                href = title_link.get_attribute("href")

                # Stop if the paper has no usable link.
                if not href:
                    raise ValueError(f"Missing paper link: {title}")

                # Convert the relative link into a full URL.
                paper_url = urljoin(listing_page.url, href)

                # Extract the final section of the link as the paper ID.
                # rstrip("/") removes a trailing slash if one exists.
                # split("/") divides the path into pieces.
                # [-1] selects the last piece.
                paper_id = href.rstrip("/").split("/")[-1]

                # This selector matches the displayed organization badge:
                # a:has(img) = a link containing an image.
                # > = a direct child of that link.
                # span.font-medium = a span with the font-medium CSS class.
                #
                # This matches the current page structure we inspected.
                organization_locator = card.locator(
                    "a:has(img) > span.font-medium"
                )

                # None means we did not find a displayed organization.
                # It does not mean that the paper has no affiliations.
                organization = None

                # Only read the badge if the matching element exists.
                if organization_locator.count() > 0:
                    organization = (
                        organization_locator.first.inner_text().strip()
                    )

                # The inspected vote widget has role="checkbox".
                # read_count() converts its displayed count into an integer.
                votes = read_count(
                    card.locator('[role="checkbox"]')
                )

                # Select the link whose href ends with "#community".
                # This is the comment-count link on the inspected cards.
                # Other numbers on a card can represent different things.
                comments = read_count(
                    card.locator('a[href$="#community"]')
                )

                # Open this paper in the detail tab.
                # The original listing stays open in its own tab.
                open_page(detail_page, paper_url)

                # ^ means "start of the text".
                # \s+ means "one or more whitespace characters".
                # This finds the text beginning with "Published on ".
                published_locator = detail_page.get_by_text(
                    re.compile(r"^Published on\s+")
                )

                # Wait until the publication label is visible.
                published_locator.first.wait_for(state="visible")

                # Read the displayed publication date.
                # removeprefix() removes the label from the beginning.
                # Example: "Published on Sep 30" becomes "Sep 30".
                #
                # Preserve the displayed value without guessing a missing year.
                published_date = (
                    published_locator.first.inner_text()
                    .strip()
                    .removeprefix("Published on ")
                )

                # A dictionary represents one row.
                # Keys become CSV column names.
                # Values become the contents of the cells.
                record = {
                    "paper_id": paper_id,
                    "title": title,
                    "organization": organization,
                    "comments": comments,
                    "votes": votes,
                    "published_date": published_date,
                    "paper_url": paper_url,

                    # Save the actual monthly URL after any redirect.
                    "listing_url": listing_page.url,

                    # Record the collection time in UTC.
                    # isoformat() turns it into a standard date/time string.
                    "collected_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }

                # Add this paper's dictionary to the list of rows.
                records.append(record)

                # Print each row so we can inspect it before using the CSV.
                # \n inserts a blank line.
                # index + 1 shows human-friendly numbering: 1, 2, 3.
                print(f"\nPaper {index + 1}:")
                print(record)

            # Return the collected rows to the code that called this function.
            return records

        finally:
            # Run this cleanup whether collection succeeds or raises an error.
            browser.close()


def save_csv(records):
    """Save the collected rows as a CSV table."""

    # An empty list means we have nothing to export.
    if not records:
        raise RuntimeError("No paper records were collected.")

    # Create the output folder.
    # parents=True creates any missing parent folders.
    # exist_ok=True allows the folder to already exist.
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    # Build a timestamp for the filename.
    # %Y%m%d = year, month, day.
    # %H%M%S = hour, minute, second.
    # %f = microseconds, helping distinguish separate runs.
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    # Combine the output folder and CSV filename.
    output_path = OUTPUT_FOLDER / f"papers_{timestamp}.csv"

    # Open the file for writing.
    # "w" means write mode.
    # newline="" lets the csv library manage line endings.
    # utf-8-sig helps Excel recognize Unicode characters.
    # The with statement closes the file automatically afterward.
    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        # DictWriter writes dictionaries as table rows.
        # records[0] selects the first row.
        # keys() gets its column names.
        # list() turns those names into a list.
        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys()),
        )

        # Write the column names as the first line.
        writer.writeheader()

        # Write all the paper rows below the header.
        # None values become empty cells.
        writer.writerows(records)

    # Return the saved file's location.
    return output_path


def main():
    """Run collection first, then export the resulting table."""

    # Collect the data and store the returned list.
    records = collect_papers()

    # Save that list and receive the CSV path.
    output_path = save_csv(records)

    # Report the number of saved rows and the output location.
    print(f"\nSaved {len(records)} papers.")
    print(f"CSV location: {output_path}")


# Python sets __name__ to "__main__" when you execute this file directly.
# This calls main() to start the program.
# Importing this file from another script would not start collection.
if __name__ == "__main__":
    main()