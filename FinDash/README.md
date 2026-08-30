
  # Personal Finance Dashboard

  This is a code bundle for Personal Finance Dashboard. The original project is available at https://www.figma.com/design/YeK34PsvBasgVJXN30JBm3/Personal-Finance-Dashboard.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.

  ## Running with the local DuckDB

  Open two terminals in `FinDash`:

  1. `npm run api` starts the read-only DuckDB API on port 8787.
  2. `npm run dev` starts the dashboard.

  The API reads `../database/alternative_data.duckdb`. Override it with the
  `FINDASH_DB_PATH` environment variable when needed. If the API is unavailable,
  the UI falls back to its bundled demo values and shows that state in the footer.
  
