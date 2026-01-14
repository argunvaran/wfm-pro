import requests
import json
import time
import uuid
import random
import argparse
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

class LoadTester:
    def __init__(self, url, tenant_id, total_requests, concurrency, delay_ms):
        self.url = url
        self.tenant_id = tenant_id
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.delay = delay_ms / 1000.0
        self.success_count = 0
        self.fail_count = 0
        self.lock = threading.Lock()

    def generate_payload(self):
        """
        Generates a valid PBX payload for the system.
        You can modify field sizes here.
        """
        call_uuid = str(uuid.uuid4())
        # Random duration between 10s and 600s
        duration = random.randint(10, 600)
        # Random Queue
        queues = ['Sales', 'Support', 'Tech', 'Retention', 'General']
        queue = random.choice(queues)
        
        return {
            "tenant_id": self.tenant_id,
            "event_type": "call_ended",
            "call_id": call_uuid,
            "caller": f"555{random.randint(1000000, 9999999)}",
            "queue": queue,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }

    def send_request(self):
        payload = self.generate_payload()
        try:
            start = time.time()
            response = requests.post(self.url, json=payload, timeout=5)
            duration = time.time() - start
            
            if response.status_code in [200, 201]:
                with self.lock:
                    self.success_count += 1
                # print(f"Valid: {duration:.3f}s")
            else:
                with self.lock:
                    self.fail_count += 1
                print(f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            with self.lock:
                self.fail_count += 1
            print(f"Error: {e}")

    def run(self):
        print(f"Starting Load Test on {self.url}")
        print(f"Tenant: {self.tenant_id}")
        print(f"Total Requests: {self.total_requests}")
        print(f"Concurrency: {self.concurrency}")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Launch tasks
            futures = []
            for _ in range(self.total_requests):
                futures.append(executor.submit(self.send_request))
                if self.delay > 0:
                    time.sleep(self.delay)
                    
            # Wait for all
            for f in futures:
                f.result()
                
        total_time = time.time() - start_time
        print("\n--- Test Completed ---")
        print(f"Time Taken: {total_time:.2f}s")
        print(f"RPS: {self.total_requests / total_time:.2f}")
        print(f"Success: {self.success_count}")
        print(f"Failed: {self.fail_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WFM Webhook Load Tester')
    parser.add_argument('--url', type=str, default='http://localhost:8000/api/webhook/', help='Target URL')
    parser.add_argument('--tenant', type=str, required=True, help='Tenant Schema Name (api key)')
    parser.add_argument('--count', type=int, default=100, help='Total requests to send')
    parser.add_argument('--workers', type=int, default=10, help='Concurrent workers')
    parser.add_argument('--delay', type=int, default=0, help='Delay between requests in ms')
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url, args.tenant, args.count, args.workers, args.delay)
    tester.run()
