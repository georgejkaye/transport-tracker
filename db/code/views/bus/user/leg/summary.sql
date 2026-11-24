DROP VIEW IF EXISTS transport_user_bus_leg_summary_view;

CREATE OR REPLACE VIEW transport_user_bus_leg_summary_view
AS
SELECT
    leg_id,