from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Optional, Callable, Pattern, Union


class CustomFilter(BaseFilter):
    def __init__(
        self,
        pattern: Optional[str] = None,
        startswith: Optional[str] = None,
        endswith: Optional[str] = None,
        regex: Optional[Pattern] = None,
        condition: Optional[Callable[[Union[Message, CallbackQuery]], bool]] = None
    ) -> None:
        if sum([bool(pattern), bool(startswith), bool(endswith), bool(regex), bool(condition)]) > 1:
            raise ValueError(
                "You can only use one of 'pattern', 'startswith', 'endswith', 'regex', or 'condition'"
            )
        elif pattern:
            self._mode = "exact"
            self._text = pattern
        elif startswith:
            self._mode = "startswith"
            self._text = startswith
        elif endswith:
            self._mode = "endswith"
            self._text = endswith
        elif regex:
            self._mode = "regex"
            self._regex = regex
        elif condition:
            self._mode = "custom"
            self._condition = condition
        else:
            raise ValueError(
                "You must specify at least one parameter: 'pattern', 'startswith', 'endswith', 'regex', or 'condition'"
            )

    async def __call__(self, data: Union[Message, CallbackQuery]) -> bool:
        if self._mode == "exact":
            return (data.text if isinstance(data, Message) else data.data) == self._text
        elif self._mode == "startswith":
            return (data.text if isinstance(data, Message) else data.data).startswith(self._text)
        elif self._mode == "endswith":
            return (data.text if isinstance(data, Message) else data.data).endswith(self._text)
        elif self._mode == "regex":
            content = data.text if isinstance(data, Message) else data.data
            return bool(content and self._regex.search(content))
        elif self._mode == "custom":
            return self._condition(data)
        return False