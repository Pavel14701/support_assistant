from application.interfaces import MessagePaginator

class PaginatorGateway(MessagePaginator):
    def __init__(self, config):
        """
        Initializes the PaginatorGateway with the given configuration.
        :param config: An instance containing max_length configuration.
        """
        self._config = config

    async def paginate_text(self, text: str) -> list[str]:
        """
        Splits the input text into chunks between 2048 and 4096 characters,
        ensuring the last chunks are distributed evenly.

        :param text: The input text to be paginated.
        :return: A list of text chunks.
        """
        min_length = 2048
        max_length = 4096
        chunks = []
        i = 0
        while i < len(text):
            chunk_size = max_length if (len(text) - i) > max_length \
                else min(max_length, len(text) - i)
            chunks.append(text[i:i + chunk_size])
            i += chunk_size
        if len(chunks[-1]) < min_length:
            last_chunk = chunks.pop()
            total_length = sum(len(chunk) for chunk in chunks) + len(last_chunk)
            avg_length = total_length // len(chunks)
            redistributed_chunks = []
            start = 0
            for _ in range(len(chunks)):
                redistributed_chunks.append(text[start:start + avg_length])
                start += avg_length
            redistributed_chunks.append(text[start:])
            return redistributed_chunks
        return chunks
