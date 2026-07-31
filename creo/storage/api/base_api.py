from creo.utils.runtime_settings import get_youtube_key, get_instagram_key, get_whatsapp_key


class BaseApiRepository:
    @property
    def use_real_api(self) -> bool:
        return self._check_key()

    def _check_key(self) -> bool:
        raise NotImplementedError

    def _mock_data(self):
        raise NotImplementedError
