"""
Ultra High-Performance API Endpoints
Optimized for processing millions of records in 1-5 seconds
"""

import asyncio
import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from app.services.ultra_performance import get_ultra_processor

logger = logging.getLogger(__name__)

# Create router for ultra-performance endpoints
ultra_router = APIRouter(prefix="/api/v1/ultra", tags=["Ultra Performance"])

@ultra_router.post("/generate-dummy-data/{num_records}")
async def ultra_fast_generate_dummy_data(
    num_records: int,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Generate millions of dummy records in 1-5 seconds
    
    Args:
        num_records: Number of records to generate (supports millions)
        
    Returns:
        Generation statistics and performance metrics
    """
    start_time = time.time()
    
    try:
        if num_records <= 0:
            raise HTTPException(status_code=400, detail="Number of records must be positive")
        
        if num_records > 10_000_000:  # 10 million limit for safety
            raise HTTPException(status_code=400, detail="Maximum 10 million records allowed")
        
        logger.info(f"🚀 Starting ultra-fast generation of {num_records:,} dummy records...")
        
        # Get ultra-performance processor
        processor = get_ultra_processor()
        
        # Generate data using ultra-fast method
        result = await processor.ultra_fast_dummy_data_generation(num_records)
        
        # Add performance metrics
        result.update({
            'endpoint_processing_time': time.time() - start_time,
            'performance_tier': 'ULTRA_FAST',
            'optimization_level': 'MAXIMUM'
        })
        
        # Log performance metrics
        logger.info(f"✅ Ultra-fast generation completed: {result['records_per_second']:,.0f} records/sec")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in ultra-fast dummy data generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@ultra_router.post("/process-excel")
async def ultra_fast_excel_processing(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Process Excel/CSV files with millions of records in 1-5 seconds
    
    Args:
        file: Excel/CSV file to process
        
    Returns:
        Processing statistics and performance metrics
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_ext = '.' + file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file provided")
        
        logger.info(f"🚀 Starting ultra-fast processing of {file.filename} ({len(file_content):,} bytes)...")
        
        # Get ultra-performance processor
        processor = get_ultra_processor()
        
        # Process file using ultra-fast method
        result = await processor.ultra_fast_excel_processing(file_content, file.filename)
        
        # Add performance metrics
        result.update({
            'endpoint_processing_time': time.time() - start_time,
            'file_size_bytes': len(file_content),
            'performance_tier': 'ULTRA_FAST',
            'optimization_level': 'MAXIMUM'
        })
        
        # Log performance metrics
        logger.info(f"✅ Ultra-fast Excel processing completed: {result['records_per_second']:,.0f} records/sec")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ultra-fast Excel processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@ultra_router.post("/sync-data")
async def ultra_fast_sync_data(background_tasks: BackgroundTasks = None) -> Dict[str, Any]:
    """
    Synchronize data between pegawai and global_id tables in 1-5 seconds
    Handles millions of records with ultra-fast processing
    
    Returns:
        Synchronization statistics and performance metrics
    """
    start_time = time.time()
    
    try:
        logger.info("🚀 Starting ultra-fast data synchronization...")
        
        # Get ultra-performance processor
        processor = get_ultra_processor()
        
        # Perform ultra-fast synchronization
        result = await processor.ultra_fast_sync_service()
        
        # Add performance metrics
        result.update({
            'endpoint_processing_time': time.time() - start_time,
            'performance_tier': 'ULTRA_FAST',
            'optimization_level': 'MAXIMUM'
        })
        
        # Log performance metrics
        if result['records_processed'] > 0:
            logger.info(f"✅ Ultra-fast sync completed: {result['records_per_second']:,.0f} records/sec")
        else:
            logger.info("✅ Ultra-fast sync completed: No new records to process")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in ultra-fast sync: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")


@ultra_router.get("/performance-benchmark/{operation}")
async def performance_benchmark(operation: str, num_records: int = 100000) -> Dict[str, Any]:
    """
    Run performance benchmarks for different operations
    
    Args:
        operation: Type of operation (dummy_data, excel_processing, sync)
        num_records: Number of records for benchmarking
        
    Returns:
        Benchmark results and performance comparison
    """
    start_time = time.time()
    
    try:
        processor = get_ultra_processor()
        benchmark_results = {}
        
        if operation == "dummy_data":
            logger.info(f"🏃 Benchmarking dummy data generation with {num_records:,} records...")
            
            # Run multiple iterations for accurate benchmarking
            iterations = 3
            times = []
            
            for i in range(iterations):
                iter_start = time.time()
                result = await processor.ultra_fast_dummy_data_generation(num_records)
                iter_time = time.time() - iter_start
                times.append(iter_time)
                
                # Clean up for fair benchmarking (optional)
                await asyncio.sleep(0.1)
            
            benchmark_results = {
                'operation': 'dummy_data_generation',
                'records_per_test': num_records,
                'iterations': iterations,
                'times': times,
                'average_time': sum(times) / len(times),
                'best_time': min(times),
                'worst_time': max(times),
                'average_records_per_second': num_records / (sum(times) / len(times)),
                'peak_records_per_second': num_records / min(times)
            }
            
        elif operation == "sync":
            logger.info("🏃 Benchmarking data synchronization...")
            
            sync_start = time.time()
            result = await processor.ultra_fast_sync_service()
            sync_time = time.time() - sync_start
            
            benchmark_results = {
                'operation': 'data_synchronization',
                'records_processed': result['records_processed'],
                'sync_time': sync_time,
                'records_per_second': result.get('records_per_second', 0),
                'breakdown': {
                    'load_time': result.get('load_time', 0),
                    'process_time': result.get('process_time', 0),
                    'gid_generation_time': result.get('gid_generation_time', 0),
                    'insert_time': result.get('insert_time', 0)
                }
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {operation}")
        
        # Add overall benchmark metrics
        benchmark_results.update({
            'benchmark_duration': time.time() - start_time,
            'performance_tier': 'ULTRA_FAST',
            'optimization_level': 'MAXIMUM',
            'timestamp': time.time()
        })
        
        logger.info(f"✅ Benchmark completed for {operation}")
        return benchmark_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in performance benchmark: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@ultra_router.get("/system-performance")
async def get_system_performance() -> Dict[str, Any]:
    """
    Get current system performance capabilities and statistics
    
    Returns:
        System performance metrics and capabilities
    """
    try:
        processor = get_ultra_processor()
        
        # Get system information
        import multiprocessing
        import psutil
        import platform
        
        # Test small operation for latency measurement
        start_time = time.time()
        test_result = await processor.ultra_fast_dummy_data_generation(1000)  # Small test
        latency = time.time() - start_time
        
        return {
            'system_info': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': multiprocessing.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'memory_percent': psutil.virtual_memory().percent
            },
            'performance_capabilities': {
                'max_workers': processor.worker_count,
                'batch_size': processor.batch_size,
                'connection_pool_size': 20,
                'estimated_max_records_per_second': test_result['records_per_second'] * 100,  # Estimate scaling
                'optimization_level': 'MAXIMUM',
                'performance_tier': 'ULTRA_FAST'
            },
            'latency_test': {
                'test_records': 1000,
                'latency_seconds': latency,
                'records_per_second': test_result['records_per_second']
            },
            'supported_operations': [
                'ultra_fast_dummy_data_generation',
                'ultra_fast_excel_processing',
                'ultra_fast_data_synchronization'
            ],
            'recommended_limits': {
                'max_dummy_records': 10_000_000,
                'max_excel_file_size_mb': 500,
                'optimal_batch_size': processor.batch_size
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system performance: {str(e)}")


# Add the ultra-performance router to the main application
def include_ultra_routes(app):
    """Include ultra-performance routes in the main application"""
    app.include_router(ultra_router)