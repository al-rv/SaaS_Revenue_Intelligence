-- Raw table ingestion
-- Placeholder token {{RAW_DATA_DIR}} is replaced by build script

CREATE OR REPLACE TABLE raw.accounts AS
SELECT *
FROM read_csv_auto('{{RAW_DATA_DIR}}/ravenstack_accounts.csv', header = true);

CREATE OR REPLACE TABLE raw.subscriptions AS
SELECT *
FROM read_csv_auto('{{RAW_DATA_DIR}}/ravenstack_subscriptions.csv', header = true);

CREATE OR REPLACE TABLE raw.feature_usage AS
SELECT *
FROM read_csv_auto('{{RAW_DATA_DIR}}/ravenstack_feature_usage.csv', header = true);

CREATE OR REPLACE TABLE raw.support_tickets AS
SELECT *
FROM read_csv_auto('{{RAW_DATA_DIR}}/ravenstack_support_tickets.csv', header = true);

CREATE OR REPLACE TABLE raw.churn_events AS
SELECT *
FROM read_csv_auto('{{RAW_DATA_DIR}}/ravenstack_churn_events.csv', header = true);
