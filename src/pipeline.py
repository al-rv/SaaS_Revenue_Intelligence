"""Orchestrate warehouse build and dashboard expoet steps"""

from __future__ import annotations

from scripts.build_warehouse import main as build_warehouse
from scripts.export_for_app import main as export_for_app

def run_build() -> None:
    build_warehouse()
    
def run_export() -> None:
    export_for_app()
    
def run_pipeline() -> None:
    """Run the full analytics pipeline: SQL warehouse build hten parquet export"""
    run_build()
    run_export()
    
if __name__ == "__main__":
    run_pipeline()