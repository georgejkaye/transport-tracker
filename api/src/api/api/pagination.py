from dataclasses import dataclass


@dataclass
class Page[T]:
    page_size: int
    total_pages: int
    current_page: int
    items: list[T]
