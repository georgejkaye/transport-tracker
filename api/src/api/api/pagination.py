from dataclasses import dataclass


@dataclass
class Page[T]:
    total_pages: int
    current_page: int
    items: list[T]
