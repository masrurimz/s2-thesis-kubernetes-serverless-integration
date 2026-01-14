"""Pytest fixtures for controller tests."""
import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def temp_db():
    """Create temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    db_path.unlink(missing_ok=True)


@pytest.fixture
def mock_haproxy_stats():
    """Mock HAProxy stats CSV response."""
    return """# pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq,dresp,ereq,econ,eresp,wretr,wredis,status,weight,act,bck,chkfail,chkdown,lastchg,downtime,qlimit,pid,iid,sid,throttle,lbtot,tracked,type,rate,rate_lim,rate_max,check_status,check_code,check_duration,hrsp_1xx,hrsp_2xx,hrsp_3xx,hrsp_4xx,hrsp_5xx,hrsp_other,hanafail,req_rate,req_rate_max,req_tot,cli_abrt,srv_abrt,comp_in,comp_out,comp_byp,comp_rsp,lastsess,last_chk,last_agt,qtime,ctime,rtime,ttime,
servers,k3s-cluster,0,0,0,1,100,1000,50000,100000,0,0,0,0,0,0,0,UP,80,1,0,0,0,3600,0,,1,2,1,,1000,,2,0,,10,L4OK,,0,0,950,0,50,0,0,,0,,0,0,0,0,0,0,0,,,0,0,0,0,
servers,serverless-sim,0,0,0,1,100,250,12500,25000,0,0,0,0,0,0,0,UP,20,1,0,0,0,3600,0,,1,2,2,,250,,2,0,,5,L4OK,,0,0,240,0,10,0,0,,0,,0,0,0,0,0,0,0,,,0,0,0,0,
servers,BACKEND,0,0,0,2,200,1250,62500,125000,0,0,,0,0,0,0,UP,100,1,0,,0,3600,0,,1,2,0,,1250,,1,0,,15,,,,0,1190,0,60,0,0,,,,0,0,0,0,0,0,0,,,0,0,0,0,
"""


@pytest.fixture
def sample_traffic_data():
    """Sample traffic data for testing."""
    import numpy as np
    
    base_time = datetime.now()
    data = []
    for i in range(100):
        data.append({
            'timestamp': int((base_time + timedelta(seconds=i * 30)).timestamp()),
            'total_requests': 100 + i % 20,
            'avg_response_time': 25.0 + (i % 10),
            'error_rate': 0.01 * (i % 5),
            'k3s_requests': 80 + i % 15,
            'knative_requests': 20 + i % 5,
            'k3s_weight': 80,
            'knative_weight': 20
        })
    return pd.DataFrame(data)


@pytest.fixture
def mock_prediction_response():
    """Mock prediction API response."""
    return {
        'predicted_requests': 1200,
        'confidence': 0.85,
        'model_rmse': 50.0,
        'model_r2': 0.75
    }
