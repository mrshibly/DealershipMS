import random
from locust import HttpUser, task, between

class DMSUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # We assume a valid auth flow. Since we want to test load on endpoints,
        # we authenticate once or use a pre-authenticated header.
        # We can perform a mock login to obtain JWT.
        # In a test environment, seed_demo creates an admin user (admin@example.com / password)
        try:
            response = self.client.post("/api/v1/auth/login", data={
                "username": "admin@example.com",
                "password": "password"
            })
            if response.status_code == 200:
                token = response.json().get("access_token")
                self.headers = {"Authorization": f"Bearer {token}"}
            else:
                self.headers = {}
        except Exception:
            self.headers = {}

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/dashboard/snapshot", headers=self.headers)
        self.client.get("/api/v1/dashboard/analytics?period=monthly", headers=self.headers)

    @task(1)
    def view_daybook_report(self):
        # Queries for today's daybook
        self.client.get("/api/v1/reports/daybook?date=2026-06-12", headers=self.headers)

    @task(2)
    def list_products(self):
        self.client.get("/api/v1/products?page=1&per_page=10", headers=self.headers)
