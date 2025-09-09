#!/usr/bin/env python3
"""
Script to run the microservices architecture
"""

import subprocess
import sys
import time
import requests
import json
from typing import Dict, Any

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_service_health(url: str, service_name: str) -> bool:
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # For frontend, just check if it responds (no JSON expected)
            if service_name == "Frontend":
                print(f"✅ {service_name} is healthy: responding")
                return True
            else:
                data = response.json()
                print(f"✅ {service_name} is healthy: {data.get('status', 'unknown')}")
                return True
        else:
            print(f"❌ {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name} is not responding: {e}")
        return False
    except ValueError as e:
        # JSON decode error for frontend
        if service_name == "Frontend":
            print(f"✅ {service_name} is healthy: responding (non-JSON)")
            return True
        else:
            print(f"❌ {service_name} JSON decode error: {e}")
            return False

def wait_for_services():
    """Wait for all services to be healthy"""
    services = [
        ("http://localhost:8001/health", "Data Service"),
        ("http://localhost:8000/health", "Momentum Service"),
        ("http://localhost:3000", "Frontend")
    ]
    
    print("\n⏳ Waiting for services to be healthy...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        all_healthy = True
        for url, name in services:
            if not check_service_health(url, name):
                all_healthy = False
                break
        
        if all_healthy:
            print("\n🎉 All services are healthy!")
            return True
        
        attempt += 1
        print(f"⏳ Attempt {attempt}/{max_attempts} - waiting 10 seconds...")
        time.sleep(10)
    
    print("\n❌ Services failed to become healthy within timeout")
    return False

def test_microservices():
    """Test the microservices functionality"""
    print("\n🧪 Testing microservices functionality...")
    
    # Test data service
    try:
        response = requests.get("http://localhost:8001/stocks?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data Service: Retrieved {data.get('count', 0)} stocks")
        else:
            print(f"❌ Data Service test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Data Service test failed: {e}")
    
    # Test momentum service
    try:
        response = requests.get("http://localhost:8000/momentum?limit=5&top_n=3")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Momentum Service: Calculated momentum for {data.get('count', 0)} stocks")
        else:
            print(f"❌ Momentum Service test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Momentum Service test failed: {e}")
    
    # Test configuration
    try:
        response = requests.get("http://localhost:8000/config/momentum")
        if response.status_code == 200:
            data = response.json()
            weights_sum = data.get('weights_sum', 0)
            print(f"✅ Configuration: Weights sum to {weights_sum}")
        else:
            print(f"❌ Configuration test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

def main():
    """Main function"""
    print("🚀 Starting Momentum Calculator Microservices Architecture")
    print("=" * 60)
    
    # Stop any existing containers
    run_command("docker-compose -f docker-compose-microservices.yml down", "Stopping existing containers")
    
    # Build and start services
    if not run_command("docker-compose -f docker-compose-microservices.yml up --build -d", "Building and starting microservices"):
        print("❌ Failed to start microservices")
        sys.exit(1)
    
    # Wait for services to be healthy
    if not wait_for_services():
        print("❌ Services failed to start properly")
        sys.exit(1)
    
    # Test functionality
    test_microservices()
    
    print("\n" + "=" * 60)
    print("🎉 Microservices Architecture is running!")
    print("\n📋 Service URLs:")
    print("  • Frontend: http://localhost:3000")
    print("  • Momentum Service (Main API): http://localhost:8000")
    print("  • Data Service: http://localhost:8001")
    print("  • Nginx Load Balancer: http://localhost:80")
    print("\n📚 API Documentation:")
    print("  • Momentum Service: http://localhost:8000/docs")
    print("  • Data Service: http://localhost:8001/docs")
    print("\n🛠️  Management Commands:")
    print("  • Stop services: docker-compose -f docker-compose-microservices.yml down")
    print("  • View logs: docker-compose -f docker-compose-microservices.yml logs -f")
    print("  • Restart services: docker-compose -f docker-compose-microservices.yml restart")

if __name__ == "__main__":
    main()
