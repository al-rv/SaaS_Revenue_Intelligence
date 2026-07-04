# Architecture

The project follows a production-style analytics architecture: raw source files are ingested into DuckDB, transformed through SQL layers, validated, exported to dashboard-ready files, and served through Streamlit.
