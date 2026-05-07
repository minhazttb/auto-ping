"""
Async Ping Engine
Performs concurrent ICMP pings with retry logic
"""

import asyncio
from icmplib import async_ping, SocketPermissionError
import yaml
from typing import List, Dict
import subprocess
import platform


class PingEngine:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize ping engine with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['ping']
        
        self.timeout = self.config['timeout_seconds']
        self.retry_count = self.config['retry_count']
        self.concurrent_limit = self.config['concurrent_limit']
        self.packet_count = self.config['packet_count']
        self.privileged = self.config['privileged_mode']
        self.use_fallback = False
    
    async def _ping_with_icmplib(self, ip: str) -> Dict[str, any]:
        """Ping using icmplib (preferred method)"""
        try:
            host = await async_ping(
                ip,
                count=self.packet_count,
                timeout=self.timeout,
                privileged=self.privileged
            )
            
            return {
                'ip': ip,
                'status': 'UP' if host.is_alive else 'DOWN',
                'latency': round(host.avg_rtt, 2) if host.is_alive else None,
                'packet_loss': host.packet_loss
            }
            
        except SocketPermissionError:
            # Fall back to system ping if permission denied
            self.use_fallback = True
            return await self._ping_with_subprocess(ip)
        except Exception as e:
            return {
                'ip': ip,
                'status': 'ERROR',
                'latency': None,
                'error': str(e)
            }
    
    async def _ping_with_subprocess(self, ip: str) -> Dict[str, any]:
        """Fallback ping using system command"""
        try:
            # Windows ping command
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
            
            command = ['ping', param, str(self.packet_count), timeout_param, str(self.timeout * 1000), ip]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Check return code (0 = success)
            is_alive = process.returncode == 0
            
            return {
                'ip': ip,
                'status': 'UP' if is_alive else 'DOWN',
                'latency': None,  # Parsing latency from output is complex
                'packet_loss': 0 if is_alive else 100
            }
            
        except Exception as e:
            return {
                'ip': ip,
                'status': 'ERROR',
                'latency': None,
                'error': str(e)
            }
    
    async def _ping_single(self, ip: str, retries: int = None) -> Dict[str, any]:
        """Ping a single IP with retry logic"""
        retries = retries or self.retry_count
        
        for attempt in range(retries + 1):
            if self.use_fallback:
                result = await self._ping_with_subprocess(ip)
            else:
                result = await self._ping_with_icmplib(ip)
            
            # If UP or ERROR, return immediately
            if result['status'] in ['UP', 'ERROR']:
                return result
            
            # If DOWN and retries remaining, wait and retry
            if attempt < retries:
                await asyncio.sleep(0.5)
        
        return result
    
    async def _ping_batch(self, ips: List[str]) -> List[Dict[str, any]]:
        """Ping a batch of IPs concurrently"""
        tasks = [self._ping_single(ip) for ip in ips]
        return await asyncio.gather(*tasks)
    
    async def ping_all(self, clients: List[Dict[str, str]], progress_callback=None) -> List[Dict[str, any]]:
        """Ping all clients with batching and progress updates"""
        results = []
        total = len(clients)
        
        # Process in batches to avoid overwhelming system
        for i in range(0, total, self.concurrent_limit):
            batch = clients[i:i + self.concurrent_limit]
            batch_ips = [client['ip_address'] for client in batch]
            
            # Ping batch
            batch_results = await self._ping_batch(batch_ips)
            
            # Merge with client info
            for client, result in zip(batch, batch_results):
                combined = {
                    'client_name': client['client_name'],
                    'ip_address': result['ip'],
                    'status': result['status'],
                    'latency': result.get('latency'),
                    'pop_name': client['pop_name']
                }
                results.append(combined)
            
            # Progress callback
            if progress_callback:
                progress_callback(len(results), total)
        
        return results
    
    def ping_all_sync(self, clients: List[Dict[str, str]], progress_callback=None) -> List[Dict[str, any]]:
        """Synchronous wrapper for async ping"""
        return asyncio.run(self.ping_all(clients, progress_callback))
