#!/usr/bin/env python3
"""
Sprint 2: Historical Data Collection for Load Prediction

This module collects traffic patterns from HAProxy stats and stores them
for linear regression model training and real-time prediction.
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
import pandas as pd
import requests
import structlog

logger = structlog.get_logger(__name__)


class DataCollector:
    """Collects and stores historical traffic data from HAProxy stats."""
    
    def __init__(self, 
                 haproxy_stats_url: str = "http://localhost:8404/stats;csv",
                 db_path: str = "data/historical-patterns/traffic_patterns.db",
                 collection_interval: int = 30):
        """
        Initialize data collector.
        
        Args:
            haproxy_stats_url: HAProxy stats CSV endpoint
            db_path: SQLite database path for historical data
            collection_interval: Data collection interval in seconds
        """
        self.haproxy_stats_url = haproxy_stats_url
        self.db_path = Path(db_path)
        self.collection_interval = collection_interval
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self) -> None:
        """Initialize SQLite database with traffic patterns table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traffic_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    total_requests INTEGER NOT NULL,
                    k3s_requests INTEGER NOT NULL,
                    knative_requests INTEGER NOT NULL,
                    avg_response_time REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    k3s_weight INTEGER NOT NULL,
                    knative_weight INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON traffic_patterns(timestamp)
            """)
            
        logger.info("Database initialized", db_path=str(self.db_path))
        
    def collect_current_stats(self) -> Optional[Dict]:
        """
        Collect current traffic statistics from HAProxy.
        
        Returns:
            Dictionary with current traffic stats or None if failed
        """
        try:
            response = requests.get(self.haproxy_stats_url, timeout=5)
            response.raise_for_status()
            
            # Parse HAProxy CSV stats
            lines = response.text.strip().split('\n')
            headers = lines[0].split(',')
            
            stats = {}
            total_requests = 0
            k3s_requests = 0
            knative_requests = 0
            
            for line in lines[1:]:
                if not line.strip():
                    continue
                    
                fields = line.split(',')
                if len(fields) < len(headers):
                    continue
                    
                row = dict(zip(headers, fields))
                
                # Extract backend server stats
                if row.get('svname') == 'k3s-backend':
                    k3s_requests = int(row.get('stot', 0) or 0)
                elif row.get('svname') == 'knative-backend':
                    knative_requests = int(row.get('stot', 0) or 0)
                elif row.get('pxname') == 'hybrid-backend' and row.get('svname') == 'BACKEND':
                    total_requests = int(row.get('stot', 0) or 0)
                    
            # Calculate additional metrics
            current_time = int(time.time())
            error_rate = 0.0  # Calculate from HAProxy stats if available
            avg_response_time = 25.0  # Default based on Sprint 1 baseline
            
            # Get current weights (default to 80/20 if not available)
            k3s_weight = 80
            knative_weight = 20
            
            stats = {
                'timestamp': current_time,
                'total_requests': total_requests,
                'k3s_requests': k3s_requests,
                'knative_requests': knative_requests,
                'avg_response_time': avg_response_time,
                'error_rate': error_rate,
                'k3s_weight': k3s_weight,
                'knative_weight': knative_weight
            }
            
            logger.debug("Collected stats", **stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to collect HAProxy stats", error=str(e))
            return None
            
    def store_stats(self, stats: Dict) -> bool:
        """
        Store traffic statistics in database.
        
        Args:
            stats: Dictionary with traffic statistics
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO traffic_patterns 
                    (timestamp, total_requests, k3s_requests, knative_requests,
                     avg_response_time, error_rate, k3s_weight, knative_weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stats['timestamp'],
                    stats['total_requests'],
                    stats['k3s_requests'], 
                    stats['knative_requests'],
                    stats['avg_response_time'],
                    stats['error_rate'],
                    stats['k3s_weight'],
                    stats['knative_weight']
                ))
                
            logger.debug("Stored stats in database", timestamp=stats['timestamp'])
            return True
            
        except Exception as e:
            logger.error("Failed to store stats", error=str(e))
            return False
            
    def get_historical_data(self, 
                          hours: int = 24,
                          min_points: int = 10) -> pd.DataFrame:
        """
        Retrieve historical traffic data for model training.
        
        Args:
            hours: Number of hours of historical data to retrieve
            min_points: Minimum number of data points required
            
        Returns:
            DataFrame with historical traffic patterns
        """
        cutoff_time = int(time.time()) - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("""
                SELECT * FROM traffic_patterns 
                WHERE timestamp >= ?
                ORDER BY timestamp
            """, conn, params=(cutoff_time,))
            
        if len(df) < min_points:
            logger.warning("Insufficient historical data", 
                          points=len(df), required=min_points)
            # Generate synthetic data for initial training
            df = self._generate_synthetic_data(min_points)
            
        logger.info("Retrieved historical data", 
                   points=len(df), hours=hours)
        return df
        
    def _generate_synthetic_data(self, num_points: int) -> pd.DataFrame:
        """
        Generate synthetic traffic data for initial model training.
        
        Args:
            num_points: Number of synthetic data points to generate
            
        Returns:
            DataFrame with synthetic traffic patterns
        """
        import numpy as np
        
        # Generate realistic traffic patterns based on Sprint 1 results
        timestamps = []
        current_time = int(time.time())
        
        data = []
        for i in range(num_points):
            timestamp = current_time - (num_points - i) * self.collection_interval
            
            # Simulate realistic traffic patterns with some variation
            base_requests = 1000 + int(200 * np.sin(i * 0.1))  # Sinusoidal pattern
            noise = int(np.random.normal(0, 50))  # Random variation
            total = max(base_requests + noise, 100)
            
            # Maintain approximate 80/20 distribution with variation
            k3s_ratio = 0.8 + np.random.normal(0, 0.05)
            k3s_ratio = max(0.7, min(0.9, k3s_ratio))  # Clamp to reasonable range
            
            k3s_requests = int(total * k3s_ratio)
            knative_requests = total - k3s_requests
            
            data.append({
                'timestamp': timestamp,
                'total_requests': total,
                'k3s_requests': k3s_requests,
                'knative_requests': knative_requests,
                'avg_response_time': 23.0 + np.random.normal(0, 5),
                'error_rate': max(0, np.random.normal(0, 0.01)),
                'k3s_weight': 80,
                'knative_weight': 20
            })
            
        df = pd.DataFrame(data)
        logger.info("Generated synthetic training data", points=num_points)
        return df
        
    async def continuous_collection(self, duration_minutes: Optional[int] = None) -> None:
        """
        Run continuous data collection in background.
        
        Args:
            duration_minutes: Collection duration in minutes (None for infinite)
        """
        logger.info("Starting continuous data collection", 
                   interval=self.collection_interval)
        
        start_time = time.time()
        collection_count = 0
        
        try:
            while True:
                # Check duration limit
                if duration_minutes:
                    elapsed = (time.time() - start_time) / 60
                    if elapsed >= duration_minutes:
                        break
                        
                # Collect and store current stats
                stats = self.collect_current_stats()
                if stats:
                    if self.store_stats(stats):
                        collection_count += 1
                        
                logger.debug("Collection cycle complete", 
                           count=collection_count, timestamp=stats.get('timestamp') if stats else None)
                
                # Wait for next collection interval
                await asyncio.sleep(self.collection_interval)
                
        except KeyboardInterrupt:
            logger.info("Data collection stopped by user")
        except Exception as e:
            logger.error("Data collection failed", error=str(e))
        finally:
            logger.info("Data collection complete", 
                       total_collections=collection_count,
                       duration_minutes=(time.time() - start_time) / 60)
            
    def export_data(self, output_path: str, format: str = 'csv') -> bool:
        """
        Export historical data for analysis.
        
        Args:
            output_path: Output file path
            format: Export format ('csv', 'json', 'parquet')
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            df = self.get_historical_data(hours=168)  # Last week
            
            if format == 'csv':
                df.to_csv(output_path, index=False)
            elif format == 'json':
                df.to_json(output_path, orient='records', date_format='iso')
            elif format == 'parquet':
                df.to_parquet(output_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            logger.info("Data exported", path=output_path, format=format, records=len(df))
            return True
            
        except Exception as e:
            logger.error("Data export failed", error=str(e))
            return False


async def main():
    """Main function for testing data collection."""
    collector = DataCollector()
    
    # Test single collection
    stats = collector.collect_current_stats()
    if stats:
        collector.store_stats(stats)
        print(f"Collected: {stats}")
    
    # Test historical data retrieval
    df = collector.get_historical_data(hours=1)
    print(f"Historical data: {len(df)} points")
    print(df.head())


if __name__ == "__main__":
    asyncio.run(main())