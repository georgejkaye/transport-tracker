from typing import Optional
from bs4 import BeautifulSoup, Tag


def get_tag_by_class_name(
    soup: BeautifulSoup | Tag, class_name: str
) -> Optional[Tag]:
    result = soup.find(class_=class_name)
    if result is None or not isinstance(result, Tag):
        return None
    return result


def get_tags_by_class_name(
    soup: BeautifulSoup | Tag, class_name: str
) -> list[Tag]:
    results = soup.find_all(class_=class_name)
    return [result for result in results if isinstance(result, Tag)]


def get_tags_by_selector(soup: BeautifulSoup | Tag, selector: str) -> list[Tag]:
    return soup.select(selector)


def get_tag_by_selector(soup: BeautifulSoup | Tag, selector: str) -> Tag:
    results = get_tags_by_selector(soup, selector)
    if len(results) != 1:
        raise RuntimeError(f"Expected 1 result but got {len(results)}")
    return results[0]
