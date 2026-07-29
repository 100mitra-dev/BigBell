from creo.models import Application
from creo.utils.helpers import load_applications, save_applications


class JsonApplicationRepository:
    def list_all(self) -> list[Application]:
        return load_applications()

    def get_by_id(self, app_id: str):
        for a in self.list_all():
            if a.id == app_id:
                return a
        return None

    def save_all(self, apps: list[Application]):
        save_applications(apps)
