class GoogleSheetsClient:
    def health_check(self, *, access_token: str) -> dict:
        return {"status": "authorized_not_resource_tested"}
